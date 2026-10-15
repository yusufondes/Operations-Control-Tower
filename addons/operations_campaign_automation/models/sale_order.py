from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_compare

from .common import _EVENT_TOKEN, internal_event


PROTECTED = {
    "oct_campaign_confirmed_at", "oct_campaign_confirmation_ids",
    "oct_campaign_status", "oct_campaign_next_action", "oct_campaign_supply_date",
    "oct_campaign_blocker_id",
}


class CampaignConfirmation(models.Model):
    _name = "oct.campaign.confirmation"
    _inherit = "oct.dispatch.access"
    _description = "Protected Campaign Confirmation Event"
    _order = "sequence_no,id"

    confirmed_at = fields.Datetime(required=True, readonly=True)
    sequence_no = fields.Integer(required=True, readonly=True)
    actor_id = fields.Many2one("res.users", required=True, readonly=True, ondelete="restrict")
    _one_sequence = models.Constraint("UNIQUE(order_id,sequence_no)", "Confirmation sequence must be unique.")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    oct_campaign_pool_id = fields.Many2one("oct.campaign.pool", string="Campaign Pool", copy=False, check_company=True)
    oct_campaign_policy = fields.Selection([
        ("consumer", "Consumer Complete"), ("corporate", "Corporate Partial"),
    ], string="Campaign Shipment Policy", copy=False)
    oct_campaign_confirmed_at = fields.Datetime(string="Confirmed At", readonly=True, copy=False)
    oct_campaign_confirmation_ids = fields.One2many("oct.campaign.confirmation", "order_id", string="Confirmation History", readonly=True, copy=False)
    oct_campaign_status = fields.Selection([
        ("outside", "Outside Campaign"), ("draft", "Quotation"),
        ("missing_promise", "Missing Accepted Promise"), ("waiting_stock", "Waiting for Stock"),
        ("ready", "Ready"), ("finished", "Dispatched"), ("cancelled", "Cancelled"),
        ("supplier_delay", "Supply Risk"), ("conflict", "Configuration Conflict"),
    ], string="Campaign Status", default="outside", readonly=True, copy=False)
    oct_campaign_next_action = fields.Char(string="Next Action", readonly=True, copy=False)
    oct_campaign_supply_date = fields.Date(string="Supply Risk Date", readonly=True, copy=False)
    oct_campaign_blocker_id = fields.Many2one("operations.control.item", string="Operational Risk Item", readonly=True, copy=False, check_company=True)

    def _campaign_write_metadata(self, values):
        if not set(values).issubset(PROTECTED):
            raise AccessError(_("Invalid internal campaign metadata fields."))
        if any(order.company_id not in self.env.companies for order in self):
            raise AccessError(_("Campaign company is not active."))
        # Only validated, fixed source records and derived metadata are elevated.
        return super(SaleOrder, self.sudo()).write(values)

    def _campaign_validate_configuration(self):
        for order in self:
            pool = order.oct_campaign_pool_id
            if bool(pool) != bool(order.oct_campaign_policy):
                raise UserError(_("Choose both a campaign pool and a shipment policy, or neither."))
            if not pool:
                continue
            if not pool.active or pool.company_id != order.company_id or pool.warehouse_id != order.warehouse_id:
                raise UserError(_("The campaign needs an active pool for this order's company and warehouse."))
            physical = order.order_line.filtered(
                lambda line: not line.display_type and line.product_id and line.product_id.type != "service"
            )
            if not physical or any(
                line.product_id not in pool.product_ids or not line.product_id.is_storable
                or line.product_id.tracking != "none" for line in physical
            ):
                raise UserError(_("Campaign goods must be configured, untracked storable products."))

    @api.model_create_multi
    def create(self, vals_list):
        if any(PROTECTED.intersection(values) for values in vals_list) or any(
            f"default_{name}" in self.env.context for name in PROTECTED
        ):
            raise AccessError(_("Campaign audit/status fields are maintained by the workflow."))
        defaults = self.default_get(["oct_campaign_pool_id", "oct_campaign_policy"])
        pool_ids = {values.get("oct_campaign_pool_id", defaults.get("oct_campaign_pool_id"))
                    for values in vals_list if values.get("oct_campaign_pool_id", defaults.get("oct_campaign_pool_id"))}
        if not pool_ids:
            with self.env.cr.savepoint():
                records = super().create(vals_list)
                records._campaign_validate_configuration()
                return records
        self.check_access("create")
        if any(values.get("state", "draft") not in ("draft", "sent") for values in vals_list):
            raise UserError(_("Create campaign orders as quotations, then confirm through the workflow."))
        pools = self.env["oct.campaign.pool"].browse(sorted(pool_ids))
        with self.env.cr.savepoint():
            pools._campaign_lock()
            records = super(SaleOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).create(vals_list)
            records._campaign_validate_configuration()
            pools._campaign_reconcile()
            return records.with_env(self.env)

    def write(self, values):
        if PROTECTED.intersection(values):
            raise AccessError(_("Campaign audit/status fields are maintained by the workflow."))
        managed = self.filtered("oct_campaign_pool_id")
        proposed = self.env["oct.campaign.pool"].browse(values.get("oct_campaign_pool_id") or [])
        pools = managed.oct_campaign_pool_id | proposed
        if not pools:
            with self.env.cr.savepoint():
                result = super().write(values)
                if "oct_campaign_policy" in values:
                    self._campaign_validate_configuration()
                return result
        self.check_access("write")
        config_fields = {"oct_campaign_pool_id", "oct_campaign_policy", "warehouse_id", "company_id"}
        if config_fields.intersection(values) and any(
            order.oct_campaign_confirmed_at or order.state not in ("draft", "sent") for order in self
        ):
            raise UserError(_("Campaign policy, pool, company and warehouse are frozen after confirmation."))
        if "state" in values and not internal_event(self.env) and any(
            order.state != values["state"] for order in managed
        ):
            raise UserError(_("Use the order confirmation/cancellation workflow, not direct campaign state edits."))
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super().write(values)
            if config_fields.intersection(values):
                self._campaign_validate_configuration()
            if not internal_event(self.env):
                pools._campaign_reconcile()
                if config_fields.intersection(values):
                    self.filtered(lambda order: not order.oct_campaign_pool_id)._campaign_sync_status()
            return result

    def action_confirm(self):
        managed = self.filtered("oct_campaign_pool_id")
        if not managed:
            return super().action_confirm()
        self.check_access("write")
        with self.env.cr.savepoint():
            managed.oct_campaign_pool_id._campaign_lock()
            managed._campaign_validate_configuration()
            for order in managed:
                if order.state not in ("draft", "sent"):
                    raise UserError(_("Only a quotation can create a new campaign confirmation event."))
                order._dispatch_touch()
                moment = fields.Datetime.now()
                sequence = max(order.oct_campaign_confirmation_ids.mapped("sequence_no"), default=0) + 1
                self.env["oct.campaign.confirmation"]._workflow_create({
                    "order_id": order.id, "confirmed_at": moment,
                    "sequence_no": sequence, "actor_id": self.env.user.id,
                })
                order._campaign_write_metadata({"oct_campaign_confirmed_at": moment})
            result = super(SaleOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).action_confirm()
            managed.oct_campaign_pool_id._campaign_reconcile()
            return result

    def _action_cancel(self):
        pools = self.oct_campaign_pool_id
        if not pools:
            return super()._action_cancel()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(SaleOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN))._action_cancel()
            pools._campaign_reconcile()
            return result

    def action_draft(self):
        pools = self.oct_campaign_pool_id
        if not pools:
            return super().action_draft()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(SaleOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).action_draft()
            pools._campaign_reconcile()
            return result

    def _campaign_stock_lock(self, moves):
        """Stock-authorized narrow source lock; does not grant Sales write rights."""
        moves.check_access("write")
        moves._check_company()
        source = (moves | moves.picking_id.move_ids).sudo().sale_line_id.order_id
        orders = self.sudo().exists()
        if any(order.company_id not in self.env.companies for order in orders) or orders - source:
            raise AccessError(_("The stock operation does not authorize these campaign orders."))
        orders.oct_campaign_pool_id._campaign_lock()
        # Bounded technical revision touch after stock-write/company/link proof.
        orders._dispatch_touch()
        return orders

    def action_campaign_reconcile(self):
        self.check_access("read")
        pools = self.oct_campaign_pool_id
        if self.env.user.has_group("stock.group_stock_manager") or (
            self.env.user.has_group("stock.group_stock_user")
            and self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator")
        ):
            pools.action_reconcile()
        else:
            self._campaign_sync_status()
        return True

    def _campaign_sync_status(self):
        """Derived, source-linked operational risk; never a customer commitment."""
        self.oct_campaign_pool_id._campaign_lock()
        for order in self.sudo().exists():
            if order.company_id not in self.env.companies:
                raise AccessError(_("Campaign company is not active."))
            pool = order.oct_campaign_pool_id
            promise = order.oct_dispatch_promise_ids
            lines = order.order_line.filtered(
                lambda line: not line.display_type and line.product_id and line.product_id.type != "service"
            )
            remaining = lines.filtered(lambda line: float_compare(
                line.product_uom_qty - line.qty_delivered, 0, precision_rounding=line.product_uom_id.rounding
            ) > 0)
            supply_date = False
            if not pool:
                status, action = "outside", False
            elif order.state == "cancel":
                status, action = "cancelled", "Order cancelled; retain the confirmation and response history."
            elif order.state in ("draft", "sent"):
                status, action = "draft", "Confirm the quotation and record its accepted warehouse promise."
            elif not pool.active or pool.company_id != order.company_id or pool.warehouse_id != order.warehouse_id:
                status, action = "conflict", "Review the campaign pool configuration; do not dispatch."
            elif not remaining:
                status, action = "finished", "Physical demand is dispatched; retain the audit history."
            elif not promise.current_date:
                status, action = "missing_promise", "Dispatch coordinator must establish the accepted warehouse promise."
            else:
                ready = True
                for line in remaining:
                    moves = line.move_ids.filtered(lambda move: move.state not in ("done", "cancel")
                                                    and move.location_dest_id.usage == "customer")
                    allocated = sum(move.product_uom._compute_quantity(move.quantity, line.product_uom_id)
                                    for move in moves)
                    if float_compare(allocated, line.product_uom_qty - line.qty_delivered,
                                     precision_rounding=line.product_uom_id.rounding) < 0:
                        ready = False
                supply_date = pool._campaign_supply_risk_date(remaining.product_id, promise.current_date)
                if ready:
                    status, action = "ready", "Warehouse: verify picked quantities and complete the permitted customer dispatch."
                elif supply_date:
                    status, action = "supplier_delay", "Owner: follow up delayed inputs/production and propose a date only if needed; retain the accepted promise."
                else:
                    status, action = "waiting_stock", "Owner: follow up input receipt/production; consumer stock is retained until its full order is ready."
            values = {"oct_campaign_status": status, "oct_campaign_next_action": action,
                      "oct_campaign_supply_date": supply_date}
            blocked = status in ("missing_promise", "waiting_stock", "supplier_delay", "conflict")
            card = order.oct_campaign_blocker_id
            if blocked or card:
                card_values = {
                    "name": "Campaign dispatch risk: %s" % order.name,
                    "description": "Derived status: %s. Source order: %s. No customer message or stock movement is inferred." % (status, order.name),
                    "next_action": action or "No outstanding campaign action.",
                    "owner_id": pool.responsible_id.id,
                    "company_id": order.company_id.id, "area": "logistics",
                    "impact": "high" if blocked else "low", "priority": "1" if blocked else "0",
                    "state": "blocked" if blocked else "resolved",
                    "deadline": promise.current_date or False,
                }
                model = self.env["operations.control.item"].with_company(order.company_id)
                card = model._campaign_upsert(order, card_values)
                values["oct_campaign_blocker_id"] = card.id
            if any((order[name].id if order._fields[name].type == "many2one" else order[name]) != value
                   for name, value in values.items()):
                order._campaign_write_metadata(values)
        return True


class CampaignControlItem(models.Model):
    _inherit = "operations.control.item"

    oct_campaign_order_id = fields.Many2one("sale.order", readonly=True, copy=False, check_company=True, ondelete="restrict")
    _one_campaign_order = models.Constraint("UNIQUE(oct_campaign_order_id)", "A campaign order has only one derived risk item.")

    @api.model_create_multi
    def create(self, vals_list):
        if any("oct_campaign_order_id" in values for values in vals_list) or "default_oct_campaign_order_id" in self.env.context:
            raise AccessError(_("Campaign risk links are created only by the source workflow."))
        return super().create(vals_list)

    def write(self, values):
        if "oct_campaign_order_id" in values:
            raise AccessError(_("Campaign risk links cannot be edited."))
        return super().write(values)

    def unlink(self):
        if self.filtered("oct_campaign_order_id"):
            raise AccessError(_("Retain source-linked campaign risk history."))
        return super().unlink()

    @api.model
    def _campaign_upsert(self, order, values):
        order.ensure_one()
        if order.company_id not in self.env.companies or not order.oct_campaign_pool_id:
            raise AccessError(_("Invalid campaign risk source."))
        # One fixed source link, controlled derived values, no arbitrary user data import.
        clean = self.sudo().with_context({key: value for key, value in self.env.context.items()
                                         if not key.startswith("default_")})
        card = clean.search([("oct_campaign_order_id", "=", order.id)], limit=1)
        if card:
            card.write(values)
            return card
        return super(CampaignControlItem, clean).create({**values, "oct_campaign_order_id": order.id})


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        order_ids = {values.get("order_id") for values in vals_list if values.get("order_id")}
        orders = self.env["sale.order"].browse(sorted(order_ids))
        pools = orders.oct_campaign_pool_id
        if not pools:
            return super().create(vals_list)
        self.check_access("create")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            lines = super(SaleOrderLine, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).create(vals_list)
            if not internal_event(self.env):
                orders._campaign_validate_configuration()
                pools._campaign_reconcile()
            return lines.with_env(self.env)

    def write(self, values):
        orders = self.order_id
        if values.get("order_id"):
            orders |= self.env["sale.order"].browse(values["order_id"])
        pools = orders.oct_campaign_pool_id
        if not pools:
            return super().write(values)
        self.check_access("write")
        if "order_id" in values and self.order_id.filtered("oct_campaign_confirmed_at"):
            raise UserError(_("Confirmed campaign lines cannot be reparented to bypass shipment policy."))
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(SaleOrderLine, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).write(values)
            if not internal_event(self.env):
                orders._campaign_validate_configuration()
                pools._campaign_reconcile()
            return result

    def unlink(self):
        orders = self.order_id
        pools = orders.oct_campaign_pool_id
        if not pools:
            return super().unlink()
        self.check_access("unlink")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(SaleOrderLine, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).unlink()
            if not internal_event(self.env):
                pools._campaign_reconcile()
            return result
