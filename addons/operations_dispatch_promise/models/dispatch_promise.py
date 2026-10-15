from odoo import api, fields, models, _
from odoo.fields import Domain
from odoo.exceptions import AccessError, UserError


def calendar_date(value):
    try:
        result = fields.Date.to_date(value)
    except (ValueError, TypeError) as error:
        raise UserError("Enter a valid calendar date.") from error
    if not result:
        raise UserError("A calendar date is required.")
    return result


def required_text(value):
    if not isinstance(value, str) or not value.strip():
        raise UserError("Reason and customer response evidence must not be empty.")
    return value.strip()


class DispatchAccess(models.AbstractModel):
    _name = "oct.dispatch.access"
    _description = "Source Sales Order Access for Dispatch Records"
    _check_company_auto = True

    order_id = fields.Many2one("sale.order", required=True, readonly=True, ondelete="restrict", index=True, check_company=True)
    company_id = fields.Many2one(related="order_id.company_id", store=True, precompute=True, index=True)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        if not self.env.su:
            if not self.env["sale.order"].has_access("read"):
                domain = Domain.FALSE
            else:
                source = self.env["sale.order"]._search([], active_test=False)
                domain = Domain(domain) & Domain("order_id", "in", source)
        return super()._search(domain, offset, limit, order, active_test=active_test, bypass_access=bypass_access)

    def _check_access(self, operation):
        denied = super()._check_access(operation)
        if not self or self.env.su or not all(self.ids):
            return denied
        base_forbidden = denied[0] if denied else self.browse()
        remaining = self - base_forbidden
        if not remaining:
            return denied
        visible = self.search([("id", "in", remaining.ids)])
        if forbidden := base_forbidden | (remaining - visible):
            message = _("The source sales order is not accessible.")
            return forbidden, lambda: AccessError(message)
        return None

    def _coordinator_order(self):
        self.ensure_one()
        self.check_access("read")
        if not self.env.su and not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can change a promise."))
        order = self.order_id
        order.check_access("write")
        return order

    @api.model_create_multi
    def create(self, vals_list):
        raise AccessError(_("Use the dispatch workflow, not direct record creation."))

    def write(self, vals):
        raise AccessError(_("Dispatch history is protected. Use the workflow actions."))

    def unlink(self):
        raise AccessError(_("Dispatch promise and response history cannot be deleted."))

    def _workflow_create(self, values):
        # RPC context defaults must not manufacture finalized history or revisions.
        clean = self.with_context({key: value for key, value in self.env.context.items()
                                  if not key.startswith("default_")})
        return super(DispatchAccess, clean).create(values)


class DispatchPromise(models.Model):
    _name = "oct.dispatch.promise"
    _inherit = "oct.dispatch.access"
    _description = "Warehouse Dispatch Promise"
    _rec_name = "order_id"

    original_date = fields.Date(required=True, readonly=True)
    current_date = fields.Date(required=True, readonly=True)
    estimate_date = fields.Date(readonly=True)
    responsible_id = fields.Many2one("res.users", required=True, readonly=True, check_company=True, ondelete="restrict")
    revision = fields.Integer(default=1, readonly=True)
    proposal_ids = fields.One2many("oct.dispatch.proposal", "promise_id", readonly=True)
    _one_order = models.Constraint("UNIQUE(order_id)", "An order can have only one dispatch promise.")

    @api.model
    def establish(self, order_id, dispatch_date):
        if not self.env.su and not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can establish a promise."))
        order = self.env["sale.order"].browse(order_id).exists()
        order.ensure_one()
        order.check_access("write")
        date = calendar_date(dispatch_date)
        with self.env.cr.savepoint():
            order._dispatch_touch()
            if not order._dispatch_has_remaining(order._dispatch_snapshot()):
                raise UserError(_("A confirmed order with outstanding goods is required."))
            if self.search_count([("order_id", "=", order.id)]):
                raise UserError(_("The original promise is already established."))
            promise = self._workflow_create({
                "order_id": order.id, "original_date": date, "current_date": date,
                "responsible_id": self.env.user.id, "revision": 1, "estimate_date": False,
            })
            return promise.id

    def propose(self, proposed_date, reason):
        order = self._coordinator_order()
        date, reason = calendar_date(proposed_date), required_text(reason)
        with self.env.cr.savepoint():
            order._dispatch_touch()
            self.invalidate_recordset()
            snapshot = order._dispatch_snapshot()
            if not order._dispatch_has_remaining(snapshot):
                raise UserError(_("A confirmed order with outstanding goods is required."))
            pending = self.proposal_ids.filtered(lambda p: p.state == "pending")
            for proposal in pending:
                if proposal._applicable(snapshot):
                    raise UserError(_("Respond to the existing proposal before creating another."))
                proposal._record_response({"state": "stale"})
            proposal = self.env["oct.dispatch.proposal"]._workflow_create({
                "promise_id": self.id, "proposed_date": date, "reason": reason,
                "base_revision": self.revision, "scope_snapshot": snapshot, "state": "pending",
            })
            return proposal.id

    def set_estimate(self, estimate_date):
        order = self._coordinator_order()
        date = calendar_date(estimate_date) if estimate_date else False
        with self.env.cr.savepoint():
            order._dispatch_touch()
            super(DispatchAccess, self).write({"estimate_date": date})
        return True

    def _form_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id,
            "view_mode": "form", "views": [(False, "form")],
        }

    def action_propose(self):
        self._coordinator_order()
        return self._wizard("propose")

    def action_estimate(self):
        self._coordinator_order()
        return self._wizard("estimate")

    def _wizard(self, operation):
        return {
            "type": "ir.actions.act_window", "res_model": "oct.dispatch.wizard", "view_mode": "form", "target": "new",
            "context": {"default_operation": operation, "default_order_id": self.order_id.id, "default_promise_id": self.id},
        }


class DispatchProposal(models.Model):
    _name = "oct.dispatch.proposal"
    _inherit = "oct.dispatch.access"
    _description = "Dispatch Date Proposal and Customer Response"
    _rec_name = "proposed_date"
    _order = "id desc"

    promise_id = fields.Many2one("oct.dispatch.promise", required=True, readonly=True, ondelete="restrict", check_company=True, index=True)
    order_id = fields.Many2one(related="promise_id.order_id", store=True, precompute=True, readonly=True)
    proposed_date = fields.Date(required=True, readonly=True)
    reason = fields.Text(required=True, readonly=True)
    base_revision = fields.Integer(required=True, readonly=True)
    scope_snapshot = fields.Json(required=True, readonly=True)
    state = fields.Selection([("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("stale", "Stale")], default="pending", readonly=True, required=True)
    is_stale = fields.Boolean(compute="_compute_stale")
    response_decision = fields.Selection([("accepted", "Accepted"), ("rejected", "Rejected")], readonly=True)
    response_person = fields.Char(readonly=True)
    response_channel = fields.Selection([("email", "Email reference"), ("phone", "Phone note"), ("other", "Other reference")], readonly=True)
    response_at = fields.Datetime(readonly=True)
    response_evidence = fields.Text(readonly=True)
    response_user_id = fields.Many2one("res.users", readonly=True, ondelete="restrict")
    applied = fields.Boolean(string="Promise Date Changed", readonly=True)
    _one_pending = models.UniqueIndex("(promise_id) WHERE state = 'pending'")

    def _applicable(self, snapshot=None):
        self.ensure_one()
        order = self.order_id
        snapshot = snapshot if snapshot is not None else order._dispatch_snapshot()
        return (self.state == "pending" and self.base_revision == self.promise_id.revision
                and self.scope_snapshot == snapshot and order._dispatch_has_remaining(snapshot))

    @api.depends("state", "base_revision", "promise_id.revision", "order_id.oct_dispatch_scope_revision",
                 "order_id.order_line.qty_delivered", "order_id.order_line.move_ids.state",
                 "order_id.order_line.move_ids.quantity", "order_id.order_line.move_ids.write_date")
    def _compute_stale(self):
        for proposal in self:
            proposal.is_stale = proposal.state == "stale" or (proposal.state == "pending" and not proposal._applicable())

    def _record_response(self, values):
        result = super(DispatchAccess, self).write(values)
        # Free the partial unique index before a replacement proposal is inserted.
        self.flush_recordset(list(values))
        return result

    def respond(self, decision, person, channel, response_at, evidence):
        order = self._coordinator_order()
        if decision not in ("accepted", "rejected") or channel not in ("email", "phone", "other"):
            raise UserError(_("Choose an explicit customer decision and response channel."))
        try:
            at = fields.Datetime.to_datetime(response_at)
        except (ValueError, TypeError) as error:
            raise UserError(_("A valid customer response timestamp is required.")) from error
        if not at or at.tzinfo:
            raise UserError(_("A valid UTC customer response timestamp is required."))
        payload = {"response_decision": decision, "response_person": required_text(person),
                   "response_channel": channel, "response_at": at, "response_evidence": required_text(evidence)}
        with self.env.cr.savepoint():
            order._dispatch_touch()
            self.invalidate_recordset()
            self.promise_id.invalidate_recordset()
            if self.response_decision:
                if all(self[field] == value for field, value in payload.items()):
                    return self.state in ("accepted", "rejected")
                raise UserError(_("A finalized response cannot be replaced; create a new applicable proposal."))
            applicable = self._applicable()
            if self.state not in ("pending", "stale"):
                raise UserError(_("This proposal is already finalized."))
            if applicable and decision == "accepted":
                super(DispatchAccess, self.promise_id).write({
                    "current_date": self.proposed_date, "revision": self.promise_id.revision + 1,
                })
            self._record_response({
                **payload, "state": decision if applicable else "stale", "applied": applicable and decision == "accepted",
                "response_user_id": self.env.user.id,
            })
            return applicable

    def action_respond(self):
        self._coordinator_order()
        if self.response_decision:
            raise UserError(_("This proposal already has a recorded response."))
        action = self.promise_id._wizard("respond")
        action["context"]["default_proposal_id"] = self.id
        return action
