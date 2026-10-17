"""Immutable, manually evidenced customer approval of dated shipment batches."""
from collections import defaultdict
from math import isfinite

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.addons.operations_dispatch_promise.models.dispatch_promise import DispatchAccess, calendar_date, required_text


_PLAN_TOKEN = object()


class ShipmentPlan(models.Model):
    _name = "oct.shipment.plan"
    _inherit = "oct.dispatch.access"
    _description = "Customer Shipment Plan and Response"
    _order = "id desc"
    _rec_name = "order_id"

    reason = fields.Text(required=True, readonly=True)
    scope = fields.Json(required=True, readonly=True)
    baseline = fields.Json(required=True, readonly=True)
    row_ids = fields.One2many("oct.shipment.plan.row", "plan_id", readonly=True)
    state = fields.Selection([("pending", "Pending"), ("accepted", "Accepted"),
                              ("rejected", "Rejected"), ("stale", "Stale")], required=True, readonly=True)
    response_person = fields.Char(readonly=True)
    response_decision = fields.Selection([("accepted", "Accepted"), ("rejected", "Rejected")], readonly=True)
    response_channel = fields.Selection([("email", "Email reference"), ("phone", "Phone note"),
                                         ("other", "Other reference")], readonly=True)
    response_at = fields.Datetime(readonly=True)
    response_evidence = fields.Text(readonly=True)
    response_user_id = fields.Many2one("res.users", readonly=True, ondelete="restrict")

    @api.model
    def propose(self, order_id, rows, reason):
        order = self.env["sale.order"].browse(order_id).exists()
        order.ensure_one()
        order.check_access("write")
        if not self.env.su and not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can propose a shipment plan."))
        if not order.oct_campaign_pool_id or order.oct_campaign_policy != "corporate" or order.state != "sale":
            raise UserError(_("A confirmed corporate campaign order is required."))
        with self.env.cr.savepoint():
            order.oct_campaign_pool_id._campaign_lock()
            order._dispatch_touch()
            reason = required_text(reason)
            goods = order._shipment_goods()
            if not order.oct_dispatch_promise_ids.current_date or not goods:
                raise UserError(_("Establish the original accepted promise before proposing a shipment plan."))
            if not isinstance(rows, list) or not rows:
                raise UserError(_("Enter all remaining quantities as dated batches."))
            clean, totals, keys, dates = [], defaultdict(float), set(), {}
            for row in rows:
                if not isinstance(row, dict) or set(row) != {"batch", "line_id", "quantity", "latest_date"}:
                    raise UserError(_("Each batch row requires batch, line, quantity and latest date."))
                number = row["batch"]
                if type(number) is not int or number <= 0:
                    raise UserError(_("Batch numbers must be positive integers."))
                line = goods.filtered(lambda item: item.id == row["line_id"])
                qty = row["quantity"]
                if not line or type(qty) not in (int, float) or not isfinite(qty) or line.product_uom_id.compare(qty, 0) <= 0:
                    raise UserError(_("Choose an outstanding order line and a positive finite quantity."))
                due = calendar_date(row["latest_date"])
                key = (number, line.id)
                if key in keys or (number in dates and dates[number] != due):
                    raise UserError(_("Use one row per order line in a batch and one latest date per batch."))
                keys.add(key)
                dates[number] = due
                totals[line.id] += qty
                clean.append({"batch": number, "sale_line_id": line.id, "quantity": qty, "latest_date": due})
            if list(dates[n] for n in sorted(dates)) != sorted(dates.values()):
                raise UserError(_("Batch latest dates must follow the batch sequence."))
            if any(line.product_uom_id.compare(totals[line.id], line.product_uom_qty - line.qty_delivered) != 0 for line in goods):
                raise UserError(_("The complete plan must cover exactly every remaining physical order-line quantity."))
            pending = self.search([("order_id", "=", order.id), ("state", "=", "pending")])
            for previous in pending:
                if previous._valid():
                    raise UserError(_("Record a response to the pending plan before proposing a replacement."))
                previous._record_plan({"state": "stale"})
            plan = self._workflow_create({"order_id": order.id, "reason": reason,
                "scope": order._shipment_scope(), "baseline": {str(line.id): line.qty_delivered for line in order._shipment_goods(True)},
                "state": "pending"})
            for row in clean:
                self.env["oct.shipment.plan.row"]._workflow_create({"plan_id": plan.id, **row})
            return plan.id

    def _record_plan(self, values):
        return super(DispatchAccess, self).write(values)

    def _valid(self):
        self.ensure_one()
        if self.state not in ("pending", "accepted"):
            return False
        if self.state == "pending" and any(row.latest_date < self.order_id._shipment_today() for row in self.row_ids):
            return False
        order = self.order_id
        done = order.order_line.move_ids.filtered(lambda move: move.state == "done" and move.oct_shipment_plan_id == self)
        expected_scope = dict(self.scope)
        if self.state == "accepted":
            expected_scope["completed_moves"] = sorted(set(expected_scope["completed_moves"]) | set(done.ids))
        if order.state != "sale" or expected_scope != order._shipment_scope():
            return False
        for line in order._shipment_goods(include_complete=True):
            quantity = sum(move.product_uom._compute_quantity(move.quantity, line.product_uom_id, round=False)
                           for move in done.filtered(lambda item: item.sale_line_id == line))
            if line.product_uom_id.compare(line.qty_delivered, self.baseline.get(str(line.id), 0) + quantity) != 0:
                return False
        return True

    def _open_batches(self):
        self.ensure_one()
        result = []
        for number in sorted(set(self.row_ids.mapped("batch"))):
            rows = self.row_ids.filtered(lambda row: row.batch == number)
            delivered = []
            for row in rows:
                moves = row.sale_line_id.move_ids.filtered(lambda move: move.state == "done"
                    and move.oct_shipment_plan_id == self and move.oct_shipment_batch == number)
                quantity = sum(move.product_uom._compute_quantity(move.quantity, row.sale_line_id.product_uom_id, round=False) for move in moves)
                delivered.append(row.sale_line_id.product_uom_id.compare(quantity, row.quantity))
            if all(value == 0 for value in delivered):
                continue
            if any(value >= 0 for value in delivered):
                raise UserError(_("Shipment history does not match the approved batch; review the plan."))
            result.append(rows)
        return result

    def respond(self, decision, person, channel, response_at, evidence):
        order = self._coordinator_order()
        if decision not in ("accepted", "rejected") or channel not in ("email", "phone", "other"):
            raise UserError(_("Choose an explicit decision and response channel."))
        try:
            at = fields.Datetime.to_datetime(response_at)
        except (TypeError, ValueError) as error:
            raise UserError(_("Enter a valid UTC response timestamp.")) from error
        if not at or at.tzinfo:
            raise UserError(_("Enter a valid UTC response timestamp."))
        payload = {"response_decision": decision, "response_person": required_text(person), "response_channel": channel,
                   "response_at": at, "response_evidence": required_text(evidence)}
        with self.env.cr.savepoint():
            order.oct_campaign_pool_id._campaign_lock()
            order._dispatch_touch()
            self.invalidate_recordset()
            if self.response_at:
                if all(self[name] == value for name, value in payload.items()):
                    return self.state in ("accepted", "rejected")
                raise UserError(_("A recorded response cannot be changed; propose a new remaining plan."))
            valid = self._valid()
            if decision == "accepted" and valid:
                prepared = order.order_line.move_ids.filtered(lambda move: move.state not in ("done", "cancel") and move.picked)
                if prepared:
                    raise UserError(_("Review and unprepare existing work before accepting a replacement shipment plan."))
            self._record_plan({**payload, "state": decision if valid else "stale", "response_user_id": self.env.user.id})
            order.oct_campaign_pool_id._campaign_reconcile()
            return valid

    def action_respond(self):
        self._coordinator_order()
        return {"type": "ir.actions.act_window", "res_model": "oct.shipment.plan.wizard", "view_mode": "form",
                "target": "new", "context": {"default_order_id": self.order_id.id,
                "default_plan_id": self.id, "default_operation": "respond"}}


class ShipmentPlanRow(models.Model):
    _name = "oct.shipment.plan.row"
    _inherit = "oct.dispatch.access"
    _description = "Immutable Shipment Plan Batch Row"
    _order = "batch,id"

    plan_id = fields.Many2one("oct.shipment.plan", required=True, readonly=True, ondelete="restrict", check_company=True)
    order_id = fields.Many2one(related="plan_id.order_id", store=True, precompute=True, readonly=True)
    batch = fields.Integer(required=True, readonly=True)
    sale_line_id = fields.Many2one("sale.order.line", required=True, readonly=True, ondelete="restrict", check_company=True)
    quantity = fields.Float(required=True, readonly=True, digits="Product Unit")
    latest_date = fields.Date(required=True, readonly=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    oct_shipment_plan_ids = fields.One2many("oct.shipment.plan", "order_id", readonly=True, copy=False)
    oct_shipment_scope_revision = fields.Integer(readonly=True, copy=False, default=0)
    oct_shipment_plan_status = fields.Char(compute="_compute_shipment_plan_status", string="Shipment Approval Status")

    @api.depends("oct_campaign_policy", "state", "oct_shipment_scope_revision", "order_line.qty_delivered",
                 "oct_shipment_plan_ids.state", "oct_shipment_plan_ids.row_ids.latest_date")
    def _compute_shipment_plan_status(self):
        for order in self:
            if order.oct_campaign_policy != "corporate":
                order.oct_shipment_plan_status = False
                continue
            plan = order._shipment_current_plan()
            if not plan:
                status = "No accepted batch plan: full remaining shipment only."
            elif not plan._valid():
                status = "Order scope changed: renewed customer approval required."
            else:
                batches = plan._open_batches()
                if not batches:
                    status = "Approved batches completed."
                elif batches[0][0].latest_date < order._shipment_today():
                    status = "Latest dispatch date missed: renewed customer approval required."
                else:
                    status = "Next approved batch: %s. Latest dispatch: %s. Early dispatch allowed." % (
                        batches[0][0].batch, batches[0][0].latest_date)
            order.oct_shipment_plan_status = status

    @api.model_create_multi
    def create(self, vals_list):
        names = {"oct_shipment_plan_ids", "oct_shipment_scope_revision"}
        if any(names.intersection(values) for values in vals_list) or any(f"default_{name}" in self.env.context for name in names):
            raise AccessError(_("Use the shipment plan workflow."))
        return super().create(vals_list)

    def write(self, values):
        if {"oct_shipment_plan_ids", "oct_shipment_scope_revision"}.intersection(values):
            raise AccessError(_("Use the shipment plan workflow."))
        return super().write(values)

    def _shipment_goods(self, include_complete=False):
        self.ensure_one()
        return self.order_line.filtered(lambda line: not line.display_type and line.product_id
            and line.product_id.type != "service" and not line.is_downpayment
            and (include_complete or line.product_uom_id.compare(line.product_uom_qty - line.qty_delivered, 0) > 0))

    def _shipment_today(self):
        self.ensure_one()
        # Business cutoff is warehouse-local, never a caller-selected RPC timezone.
        timezone = self.warehouse_id.partner_id.tz or self.company_id.partner_id.tz or "UTC"
        return fields.Date.context_today(self.with_context(tz=timezone))

    def _shipment_scope(self):
        self.ensure_one()
        return {"confirmation": self.oct_campaign_confirmation_ids[-1:].id, "revision": self.oct_shipment_scope_revision,
                "completed_moves": sorted(self.order_line.move_ids.filtered(lambda move: move.state == "done").ids),
                "lines": [{"id": line.id, "product": line.product_id.id, "uom": line.product_uom_id.id,
                           "quantity": line.product_uom_qty} for line in self._shipment_goods(True).sorted("id")]}

    def _shipment_current_plan(self):
        self.ensure_one()
        return self.env["oct.shipment.plan"].search([("order_id", "=", self.id), ("state", "=", "accepted")], limit=1)

    def _shipment_touch_scope(self):
        for order in self.filtered("oct_campaign_pool_id"):
            super(SaleOrder, order).write({"oct_shipment_scope_revision": order.oct_shipment_scope_revision + 1})

    def action_propose_shipment_plan(self):
        self.ensure_one()
        self.check_access("write")
        if not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can propose a shipment plan."))
        return {"type": "ir.actions.act_window", "res_model": "oct.shipment.plan.wizard", "view_mode": "form",
                "target": "new", "context": {"default_order_id": self.id, "default_operation": "propose"}}

    def _shipment_batch_for_dispatch(self, lines):
        self.ensure_one()
        if self.oct_campaign_policy != "corporate" or not lines:
            return None
        quantities = defaultdict(float)
        for item in lines:
            line = item.move_id.sale_line_id
            quantities[line.id] += item.product_uom_id._compute_quantity(item.quantity, line.product_uom_id, round=False)
        plan = self._shipment_current_plan()
        if not plan:
            if any(line.product_uom_id.compare(quantities[line.id], line.product_uom_qty - line.qty_delivered) != 0
                   for line in self._shipment_goods()):
                raise UserError(_("Partial dispatch needs customer approval of exact batch quantities and latest dates."))
            if self.oct_dispatch_promise_ids.current_date < self._shipment_today():
                raise UserError(_("The accepted dispatch date has passed; record customer approval of a revised plan."))
            return None
        if not plan._valid():
            raise UserError(_("The approved shipment scope changed; obtain approval of a new remaining plan."))
        batches = plan._open_batches()
        if not batches:
            raise UserError(_("No approved batch remains."))
        batch = batches[0]
        if batch[0].latest_date < self._shipment_today():
            raise UserError(_("The approved latest date has passed; obtain customer approval before dispatch."))
        expected = {row.sale_line_id.id: row.quantity for row in batch}
        if any(line.product_uom_id.compare(quantities[line.id], expected.get(line.id, 0)) != 0
               for line in self._shipment_goods()):
            raise UserError(_("Dispatch exactly the next approved batch; quantity changes need renewed customer approval."))
        return plan, batch[0].batch


class StockMove(models.Model):
    _inherit = "stock.move"

    oct_shipment_plan_id = fields.Many2one("oct.shipment.plan", readonly=True, copy=False, ondelete="restrict")
    oct_shipment_batch = fields.Integer(readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        names = {"oct_shipment_plan_id", "oct_shipment_batch"}
        if self.env.context.get("_oct_plan_token") is not _PLAN_TOKEN and (
                any(names.intersection(values) for values in vals_list)
                or any(f"default_{name}" in self.env.context for name in names)):
            raise AccessError(_("Shipment approval links are written only by validated dispatch."))
        return super().create(vals_list)

    def write(self, values):
        if {"oct_shipment_plan_id", "oct_shipment_batch"}.intersection(values) and self.env.context.get("_oct_plan_token") is not _PLAN_TOKEN:
            raise AccessError(_("Shipment approval links cannot be edited."))
        return super().write(values)

    def _campaign_assert_dispatch(self, pools, preflight=False, cancel_backorder=False):
        orders = super()._campaign_assert_dispatch(pools, preflight=preflight, cancel_backorder=cancel_backorder)
        lines = self._campaign_active_lines(preflight=preflight).sudo()
        for order in orders:
            order._shipment_batch_for_dispatch(lines.filtered(lambda line: line.move_id.sale_line_id.order_id == order))
        return orders

    def _action_done(self, cancel_backorder=False):
        with self.env.cr.savepoint():
            pools = self.env["oct.campaign.pool"]._for_moves(self)
            pools._campaign_lock()
            lines = self._campaign_active_lines().sudo()
            decisions = {}
            for order in self._campaign_linked_orders():
                result = order._shipment_batch_for_dispatch(lines.filtered(lambda line: line.move_id.sale_line_id.order_id == order))
                if result:
                    decisions[order.id] = result
            done = super()._action_done(cancel_backorder=cancel_backorder)
            for order_id, (plan, batch) in decisions.items():
                scoped = done.filtered(lambda move: move.state == "done" and move.sale_line_id.order_id.id == order_id
                                       and move.location_dest_id.usage == "customer")
                scoped.with_context(_oct_plan_token=_PLAN_TOKEN).write({"oct_shipment_plan_id": plan.id, "oct_shipment_batch": batch})
            if decisions:
                pools._campaign_reconcile()
            return done


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        with self.env.cr.savepoint():
            lines = super().create(vals_list)
            lines.order_id._shipment_touch_scope()
            return lines

    def write(self, values):
        with self.env.cr.savepoint():
            orders = self.order_id
            result = super().write(values)
            if {"product_id", "product_uom_id", "product_uom_qty", "display_type", "order_id"}.intersection(values):
                (orders | self.order_id)._shipment_touch_scope()
            return result

    def unlink(self):
        with self.env.cr.savepoint():
            orders = self.order_id
            result = super().unlink()
            orders._shipment_touch_scope()
            return result
