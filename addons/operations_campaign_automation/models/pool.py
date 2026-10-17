from psycopg2.errors import DeadlockDetected, LockNotAvailable, SerializationFailure

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare

from .common import _ALLOCATION_TOKEN


class CampaignPool(models.Model):
    _name = "oct.campaign.pool"
    _description = "Bounded Campaign Stock Pool"
    _check_company_auto = True

    name = fields.Char(required=True)
    warehouse_id = fields.Many2one("stock.warehouse", required=True, check_company=True, ondelete="restrict")
    company_id = fields.Many2one(related="warehouse_id.company_id", store=True, precompute=True, index=True)
    location_id = fields.Many2one("stock.location", required=True, check_company=True, ondelete="restrict")
    product_ids = fields.Many2many("product.product", string="Campaign Products", required=True, check_company=True)
    active = fields.Boolean(default=True)
    responsible_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user,
                                     check_company=True, ondelete="restrict")
    revision = fields.Integer(default=0, readonly=True, copy=False)
    _one_warehouse = models.Constraint("UNIQUE(warehouse_id)", "A warehouse can have only one campaign pool.")

    @api.model_create_multi
    def create(self, vals_list):
        if any("revision" in values for values in vals_list) or "default_revision" in self.env.context:
            raise AccessError(_("The allocation revision is managed internally."))
        return super().create(vals_list)

    def write(self, values):
        if "revision" in values:
            raise AccessError(_("The allocation revision is managed internally."))
        with self.env.cr.savepoint():
            self._campaign_lock()
            structural = {"warehouse_id", "location_id", "product_ids"}.intersection(values)
            orders = self.env["sale.order"].sudo().search([
                ("oct_campaign_pool_id", "in", self.ids),
                ("company_id", "in", self.company_id.ids),
                ("oct_campaign_confirmed_at", "!=", False),
            ])
            if structural and orders:
                raise UserError(_("A pool used by confirmed campaign orders cannot change its stock scope."))
            if values.get("active") is False and orders.filtered(lambda order: order.state == "sale"):
                raise UserError(_("Complete or cancel open campaign orders before disabling their pool."))
            return super().write(values)

    def unlink(self):
        self._campaign_lock()
        return super().unlink()

    @api.constrains("warehouse_id", "location_id", "product_ids")
    def _check_scope(self):
        for pool in self:
            if pool.warehouse_id.delivery_steps != "ship_only" or pool.location_id != pool.warehouse_id.lot_stock_id:
                raise ValidationError(_("Campaign pools require the warehouse stock location and one-step deliveries."))
            if not pool.product_ids or any(not p.is_storable or p.tracking != "none" for p in pool.product_ids):
                raise ValidationError(_("Campaign pools require inventory-tracked products without lot or serial tracking."))
            others = self.with_context(active_test=False).search([
                ("id", "!=", pool.id), ("warehouse_id", "=", pool.warehouse_id.id),
                ("product_ids", "in", pool.product_ids.ids),
            ])
            if others:
                raise ValidationError(_("A warehouse product can belong to only one configured campaign pool."))

    def _campaign_lock(self):
        """Stable mutex plus an ORM touch invalidates stale repeatable-read views."""
        if not self:
            return
        self.check_access("read")
        if any(pool.company_id not in self.env.companies for pool in self):
            raise AccessError(_("The campaign pool is outside the allowed companies."))
        try:
            with self.env.cr.savepoint():
                self.flush_recordset()
                locked = self.sorted("id").try_lock_for_update()
                if set(locked.ids) != set(self.ids):
                    raise UserError(_("Campaign stock is being updated. Refresh and retry."))
                self.invalidate_recordset()
                for pool in self:
                    # A stock operator may run allocation, but cannot configure pools.
                    # Elevated write is limited to this private mutex revision.
                    super(CampaignPool, pool.sudo()).write({"revision": pool.revision + 1})
                    pool.flush_recordset(["revision"])
        except (DeadlockDetected, LockNotAvailable, SerializationFailure) as error:
            raise UserError(_("Campaign stock changed. Refresh and retry.")) from error

    @api.model
    def _for_moves(self, moves):
        """Find configured pools on either side, including inactive pools."""
        if not moves:
            return self.browse()
        companies = moves.company_id
        if any(company not in self.env.companies for company in companies):
            raise AccessError(_("Stock moves are outside the allowed companies."))
        pools = self.with_context(active_test=False).search([
            ("company_id", "in", companies.ids), ("product_ids", "in", moves.product_id.ids),
        ])
        found = self.browse()
        for pool in pools:
            scoped = moves.filtered(lambda move: move.company_id == pool.company_id and move.product_id in pool.product_ids)
            locations = scoped.location_id | scoped.location_dest_id
            if any(str(pool.location_id.id) in (location.parent_path or "").split("/")
                   or str(location.id) in (pool.location_id.parent_path or "").split("/")
                   for location in locations):
                found |= pool
        # A changed configuration must not disable a linked order's guards.
        linked = moves.sudo().sale_line_id.order_id.oct_campaign_pool_id
        return (found | self.browse(linked.ids)).sorted("id")

    def action_reconcile(self):
        allowed = self.env.user.has_group("stock.group_stock_manager") or (
            self.env.user.has_group("stock.group_stock_user")
            and self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator")
        )
        if not allowed:
            raise AccessError(_("Stock management or stock and dispatch coordination rights are required."))
        self.check_access("read")
        self._campaign_reconcile()
        return True

    def _campaign_reconcile(self):
        """Reassign only unpicked campaign reservations; native stock is truth."""
        with self.env.cr.savepoint():
            self._campaign_lock()
            for pool in self.sorted("id"):
                pool._reconcile_one()
        return True

    def _reconcile_one(self):
        self.ensure_one()
        if not self.active:
            raise UserError(_("This campaign pool is inactive; review its configuration."))
        if self.warehouse_id.delivery_steps != "ship_only" or self.location_id != self.warehouse_id.lot_stock_id:
            raise UserError(_("The campaign pool no longer has a supported one-step stock source."))
        # Stock users need not read every competing Sales order. Elevation is
        # bounded to this configured company, source subtree and product set.
        moves = self.env["stock.move"].sudo().with_company(self.company_id).search([
            ("company_id", "=", self.company_id.id), ("product_id", "in", self.product_ids.ids),
            "|", ("location_id", "child_of", self.location_id.id),
            ("location_id", "parent_of", self.location_id.id),
            ("state", "not in", ["draft", "done", "cancel"]),
        ])
        managed = moves.filtered(lambda move: move.sale_line_id.order_id.oct_campaign_pool_id.id == self.id)
        outside = moves - managed
        if any(float_compare(move.product_uom_qty, move.quantity, precision_rounding=move.product_uom.rounding) > 0
               for move in outside):
            raise UserError(_("Unmanaged or unsupported demand competes for campaign stock. Resolve the conflict first."))
        for move in managed:
            order = move.sale_line_id.order_id
            if (order.company_id != self.company_id or order.warehouse_id != self.warehouse_id
                    or move.location_id != self.location_id or move.location_dest_id.usage != "customer"
                    or move.picking_type_id != self.warehouse_id.out_type_id or not move.picking_id
                    or move.procure_method != "make_to_stock" or not move.product_id.is_storable
                    or move.product_id.tracking != "none"
                    or move.move_orig_ids.filtered(lambda origin: origin.state not in ("done", "cancel"))
                    or order.oct_campaign_policy not in ("consumer", "corporate") or order.state != "sale"):
                raise UserError(_("Campaign allocation supports confirmed one-step make-to-stock customer deliveries only."))
            if any(line.sale_line_id.order_id != order for line in move.picking_id.move_ids
                   if line.state not in ("done", "cancel")):
                raise UserError(_("Mixed-order campaign pickings are unsupported."))
        # Preserve prepared whole moves and prepared lines exactly as standard
        # unreserve does. Consumer shortages keep their newly allocated stock.
        managed.filtered(lambda move: not move.picked)._do_unreserve()
        orders = self.env["sale.order"].sudo().with_company(self.company_id).search([
            ("company_id", "=", self.company_id.id), ("warehouse_id", "=", self.warehouse_id.id),
            ("oct_campaign_pool_id", "=", self.id),
        ])
        eligible = managed.filtered(lambda move: not move.picked and move.sale_line_id.order_id.oct_campaign_confirmed_at
                                    and move.sale_line_id.order_id.oct_dispatch_promise_ids.current_date)
        requests = []
        for order in eligible.sale_line_id.order_id:
            order_moves = eligible.filtered(lambda move: move.sale_line_id.order_id == order).sorted("id")
            plan = order._shipment_current_plan() if order.oct_campaign_policy == "corporate" else False
            if not plan:
                for move in order_moves:
                    requests.append((order.oct_dispatch_promise_ids.current_date, order, move, move.product_uom_qty))
                continue
            if not plan._valid():
                continue
            if any(move.move_orig_ids for move in order_moves):
                raise UserError(_("Batch plans require unchained make-to-stock customer moves."))
            used = {move.id: 0 for move in order_moves}
            protected = {}
            for line in order._shipment_goods():
                protected[line.id] = sum(move.product_uom._compute_quantity(move.quantity, line.product_uom_id, round=False)
                    for move in managed.filtered(lambda item: item.sale_line_id == line and item.picked))
            for batch in plan._open_batches():
                for row in batch:
                    line = row.sale_line_id
                    held = min(protected.get(line.id, 0), row.quantity)
                    protected[line.id] = protected.get(line.id, 0) - held
                    remaining = row.quantity - held
                    for move in order_moves.filtered(lambda item: item.sale_line_id == line):
                        demand = move.product_uom._compute_quantity(move.product_uom_qty - used[move.id], line.product_uom_id, round=False)
                        take = min(remaining, demand)
                        if line.product_uom_id.compare(take, 0) <= 0:
                            continue
                        quantity = line.product_uom_id._compute_quantity(take, move.product_uom, round=False)
                        used[move.id] += quantity
                        remaining -= take
                        requests.append((row.latest_date, order, move, quantity))
        for due, order, move, quantity in sorted(requests, key=lambda item: (
                item[0], item[1].oct_campaign_confirmed_at, item[1].id, item[2].id)):
            move.with_context(_oct_campaign_allocation_token=_ALLOCATION_TOKEN)._action_assign(force_qty=quantity)
        eligible._recompute_state()
        orders._campaign_sync_status()
