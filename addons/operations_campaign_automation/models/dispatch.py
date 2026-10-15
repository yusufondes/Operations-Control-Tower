from collections import defaultdict

from odoo import api, models, _
from odoo.exceptions import UserError

from .common import _ALLOCATION_TOKEN, _DONE_TOKEN, _EVENT_TOKEN, _PREPARATION_TOKEN


def _trusted(env, name, token):
    return env.context.get(name) is token


def _preparation_trusted(env):
    return (_trusted(env, "_oct_campaign_allocation_token", _ALLOCATION_TOKEN)
            or _trusted(env, "_oct_campaign_done_token", _DONE_TOKEN)
            or _trusted(env, "_oct_campaign_preparation_token", _PREPARATION_TOKEN))


class StockMove(models.Model):
    _inherit = "stock.move"

    def _campaign_preparation_snapshot(self):
        snapshot = {}
        for move in self._campaign_final_moves():
            if self.env["oct.campaign.pool"]._for_moves(move):
                snapshot[move.id] = move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id, round=False,
                )
        return snapshot

    def _campaign_assert_preparation_bounds(self, snapshot):
        for move in self._campaign_final_moves():
            if not self.env["oct.campaign.pool"]._for_moves(move):
                continue
            quantity = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id, round=False)
            if move.product_id.uom_id.compare(quantity, snapshot.get(move.id, 0)) > 0:
                raise UserError(_("Prepared quantity exceeds this move's allocated stock. Use Check Availability to reconcile campaign priority."))

    def _campaign_mutation_pools(self, values_list=()):
        """Resolve only existing/proposed campaign source scopes; never all pools."""
        pool_model = self.env["oct.campaign.pool"]
        pools = pool_model._for_moves(self)
        scope = {"company_id", "product_id", "location_id", "location_dest_id", "sale_line_id", "picking_id"}
        for values in values_list:
            if self and not scope.intersection(values):
                continue
            originals = list(self) or [None]
            for move in originals:
                picking_id = values.get("picking_id", move.picking_id.id if move else False)
                picking = self.env["stock.picking"].browse(picking_id or [])
                sale_line_id = values.get("sale_line_id", move.sale_line_id.id if move else False)
                sale_line = self.env["sale.order.line"].browse(sale_line_id or []).sudo()
                product_id = values.get("product_id", move.product_id.id if move else
                                        sale_line.product_id.id or self.env.context.get("default_product_id"))
                company_id = values.get("company_id", move.company_id.id if move else
                                        picking.company_id.id or sale_line.company_id.id or self.env.company.id)
                source_id = values.get("location_id", move.location_id.id if move else picking.location_id.id)
                destination_id = values.get("location_dest_id", move.location_dest_id.id if move else picking.location_dest_id.id)
                if not product_id or not (source_id or destination_id or sale_line_id):
                    continue
                proposed = self.new({"product_id": product_id, "company_id": company_id,
                                     "location_id": source_id, "location_dest_id": destination_id,
                                     "sale_line_id": sale_line_id})
                pools |= pool_model._for_moves(proposed)
        return pools.sorted("id")

    def _campaign_final_moves(self):
        # A route's intermediate OUT operation is not a customer dispatch.
        return self.filtered(lambda m: m.state not in ("done", "cancel")
                             and m.location_dest_id.usage == "customer"
                             and m.location_id.usage != "customer")

    def _campaign_linked_orders(self):
        # Bounded technical read: warehouse users need not have Sales access.
        moves = self.sudo()
        orders = (moves.sale_line_id.order_id | moves.picking_id.move_ids.sale_line_id.order_id
                  | moves.picking_id.reference_ids.sale_ids)
        return orders.filtered("oct_campaign_policy")

    def _campaign_active_lines(self, preflight=False):
        actual = self.env["stock.move.line"]
        for move in self._campaign_final_moves():
            infer_picked = preflight and move.picking_id and not any(move.picking_id.move_ids.mapped("picked"))
            if not move.picked and not infer_picked:
                continue
            lines = move.move_line_ids.filtered(lambda ml: ml.quantity > 0)
            if move.picked and any(not line.picked for line in lines):
                lines = lines.filtered("picked")
            actual |= lines
        return actual

    def _campaign_assert_dispatch(self, pools, preflight=False, cancel_backorder=False):
        finals = self._campaign_final_moves()
        orders = finals._campaign_linked_orders()
        if orders:
            orders = orders._campaign_stock_lock(finals)
        lines = finals._campaign_active_lines(preflight=preflight)
        actual = lines.move_id
        cancel_remaining = bool(cancel_backorder) or self.env.context.get("cancel_backorder") is True
        if not actual and not cancel_remaining:
            return orders

        for move in actual.sudo():
            linked = move._campaign_linked_orders()
            order = move.sale_line_id.order_id
            if linked and not order:
                raise UserError(_("Campaign dispatch contains an unmapped product. Use a supported sales delivery."))
            if not order.oct_campaign_policy:
                continue
            pool = order.oct_campaign_pool_id
            if not pool or not pool.active or pool not in pools:
                raise UserError(_("The campaign pool is missing, inactive or inconsistent."))
            if (order.state != "sale" or move.company_id != order.company_id
                    or pool.company_id != order.company_id or move.product_id != move.sale_line_id.product_id
                    or move.product_id not in pool.product_ids or not move.product_id.is_storable
                    or move.product_id.tracking != "none" or move.location_id != pool.location_id
                    or move.picking_type_id != pool.warehouse_id.out_type_id
                    or pool.warehouse_id.delivery_steps != "ship_only"
                    or move.procure_method != "make_to_stock"
                    or move.move_orig_ids.filtered(lambda m: m.state not in ("done", "cancel"))
                    or move.move_dest_ids.filtered(lambda m: m.state not in ("done", "cancel"))):
                raise UserError(_("Campaign dispatch supports only configured one-step, untracked make-to-stock goods."))
            if not order.oct_dispatch_promise_ids:
                raise UserError(_("Establish an accepted warehouse dispatch promise before dispatching this campaign order."))
            if any(ml.company_id != move.company_id or ml.product_id != move.product_id
                   or ml.location_id != pool.location_id or ml.location_dest_id.usage != "customer"
                   for ml in lines.filtered(lambda ml: ml.move_id == move)):
                raise UserError(_("Campaign dispatch move lines have inconsistent company, product or locations."))

        for order in orders:
            for sale_line in order.order_line.filtered(lambda l: l.product_id and not l.display_type):
                candidate = lines.sudo().filtered(lambda ml: ml.move_id.sale_line_id == sale_line)
                quantity = sum(ml.product_uom_id._compute_quantity(ml.quantity, sale_line.product_uom_id, round=False)
                               for ml in candidate)
                if sale_line.product_uom_id.compare(quantity, max(sale_line.product_uom_qty - sale_line.qty_delivered, 0)) > 0:
                    raise UserError(_("Campaign dispatch cannot exceed the outstanding sales quantity."))
                if (cancel_remaining and sale_line in finals.sudo().sale_line_id
                        and sale_line.product_uom_id.compare(
                            max(sale_line.product_uom_qty - sale_line.qty_delivered, 0), quantity,
                        ) > 0):
                    raise UserError(_("Campaign partial dispatch must preserve the outstanding quantity. Create a backorder, or explicitly cancel the sales order."))

        for order in orders.filtered(lambda o: o.oct_campaign_policy == "consumer"):
            outgoing = actual.sudo().filtered(lambda m: m.sale_line_id.order_id == order)
            if not outgoing:
                continue
            if len(outgoing.picking_id) != 1 or not outgoing.picking_id:
                raise UserError(_("A consumer order must leave in one complete customer picking."))
            goods = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment
                                              and l.product_id and l.product_id.type != "service"
                                              and l.product_uom_qty > 0)
            prior = self.env["stock.move"].sudo().search_count([
                ("sale_line_id", "in", goods.ids), ("state", "=", "done"),
                ("location_dest_id.usage", "=", "customer"), ("quantity", ">", 0),
                ("company_id", "=", order.company_id.id),
            ])
            if prior:
                raise UserError(_("Consumer replacements or orders with an earlier customer shipment require a separate supported workflow."))
            for sale_line in goods:
                candidate = lines.sudo().filtered(lambda ml: ml.move_id.sale_line_id == sale_line)
                quantity = sum(ml.product_uom_id._compute_quantity(ml.quantity, sale_line.product_uom_id, round=False)
                               for ml in candidate)
                remaining = max(sale_line.product_uom_qty - sale_line.qty_delivered, 0)
                if sale_line.product_uom_id.compare(quantity, remaining) != 0:
                    raise UserError(_("Every physical line of a consumer order must be dispatched completely in one picking."))

        self._campaign_assert_available(lines, pools)
        return orders

    def _campaign_assert_available(self, lines, pools):
        # Compare the complete batch, not individual lines, so duplicate products
        # cannot each consume the same stock. Preserve other moves' reservations.
        scoped = lines.filtered(lambda ml: any(
            ml.company_id == pool.company_id and ml.product_id in pool.product_ids
            and ml.location_id == pool.location_id for pool in pools))
        dimensions = defaultdict(lambda: self.env["stock.move.line"])
        for line in scoped:
            key = (line.company_id.id, line.product_id.id, line.location_id.id,
                   line.lot_id.id, line.package_id.id, line.owner_id.id)
            dimensions[key] |= line
        for key, candidates in dimensions.items():
            company_id, product_id, location_id, lot_id, package_id, owner_id = key
            domain = [("company_id", "=", company_id), ("product_id", "=", product_id),
                      ("location_id", "=", location_id), ("lot_id", "=", lot_id),
                      ("package_id", "=", package_id), ("owner_id", "=", owner_id)]
            # Exact company/source scope is checked before these technical reads.
            quants = self.env["stock.quant"].sudo().search(domain)
            others = self.env["stock.move.line"].sudo().search(domain + [
                ("id", "not in", candidates.ids), ("state", "not in", ("done", "cancel")),
            ])
            quantity = sum(candidates.mapped("quantity_product_uom"))
            protected = max(sum(others.mapped("quantity_product_uom")),
                            sum(quants.mapped("reserved_quantity")) - quantity, 0)
            available = sum(quants.mapped("quantity")) - protected
            if candidates.product_id.uom_id.compare(quantity, available) > 0:
                raise UserError(_("Dispatch would create negative stock or consume another move's reserved stock."))

    def _action_done(self, cancel_backorder=False):
        with self.env.cr.savepoint():
            self.check_access("write")
            if any(company not in self.env.companies for company in self.company_id):
                raise UserError(_("Campaign stock operation is outside the allowed companies."))
            pools = self.env["oct.campaign.pool"]._for_moves(self)
            pools._campaign_lock()
            orders = self._campaign_assert_dispatch(pools, cancel_backorder=cancel_backorder)
            nested = _trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN)
            secured = self.with_context(_oct_campaign_done_token=_DONE_TOKEN, _oct_campaign_event_token=_EVENT_TOKEN)
            result = super(StockMove, secured)._action_done(cancel_backorder=cancel_backorder)
            if not nested and not _trusted(self.env, "_oct_campaign_allocation_token", _ALLOCATION_TOKEN):
                pools._campaign_reconcile()
            if orders:
                orders._campaign_sync_status()
            return result.with_env(self.env)

    @api.model_create_multi
    def create(self, vals_list):
        with self.env.cr.savepoint():
            pools = self._campaign_mutation_pools(vals_list)
            if pools:
                pools._campaign_lock()
            moves = super().create(vals_list)
            if not _preparation_trusted(self.env):
                moves._campaign_assert_preparation_bounds({})
                if not _trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN):
                    if moves._campaign_final_moves()._campaign_linked_orders():
                        raise UserError(_("Create campaign demand through the Sales workflow; use Check Availability for allocation."))
            if not _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN):
                done = moves.filtered(lambda m: m.state == "done")
                if done and done._campaign_linked_orders():
                    raise UserError(_("Campaign stock moves must complete through validated dispatch."))
            return moves

    def write(self, values):
        with self.env.cr.savepoint():
            pools = self._campaign_mutation_pools([values])
            if pools:
                pools._campaign_lock()
            preparation_fields = {"quantity", "picked", "product_uom", "move_line_ids"}
            validate_preparation = bool(preparation_fields.intersection(values)) and not _preparation_trusted(self.env)
            snapshot = self._campaign_preparation_snapshot() if validate_preparation else {}
            trusted = _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN)
            protected = {"sale_line_id", "picking_id", "product_id", "company_id", "location_id", "location_dest_id"}
            if not trusted:
                proposed_line = self.env["sale.order.line"].browse(values.get("sale_line_id") or []).sudo()
                proposed_picking = self.env["stock.picking"].browse(values.get("picking_id") or []).sudo()
                proposed_orders = proposed_line.order_id | proposed_picking.move_ids.sale_line_id.order_id | proposed_picking.reference_ids.sale_ids
                if proposed_orders.filtered("oct_campaign_policy") and not _trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN):
                    for move in self:
                        if not move._campaign_linked_orders():
                            raise UserError(_("Outside reservations cannot be attached to campaign demand directly. Use the Sales workflow and Check Availability."))
                for move in self.filtered(lambda m: m.location_dest_id.usage == "customer"):
                    if not move._campaign_linked_orders():
                        continue
                    if values.get("state") == "done":
                        raise UserError(_("Campaign stock moves must complete through validated dispatch."))
                    lifecycle = (_trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN)
                                 or _trusted(self.env, "_oct_campaign_allocation_token", _ALLOCATION_TOKEN))
                    if not lifecycle and (
                            values.get("state") == "cancel" or {"product_uom_qty", "product_uom"}.intersection(values)):
                        raise UserError(_("Change campaign demand or cancel it through the Sales workflow, then use Check Availability."))
                    changed = {name for name in protected if name in values
                               and (move[name].id or False) != (values[name] or False)}
                    # Standard confirmation attaches a newly created move to its
                    # first picking. Detaching/replacing an existing link is not allowed.
                    if ("picking_id" in changed and not move.picking_id and values["picking_id"]
                            and move.state != "done" and not move.move_line_ids):
                        changed.remove("picking_id")
                    # A Sales-authorized quantity decrease produces an empty
                    # negative procurement move. Native _merge_moves detaches
                    # that temporary move before absorbing it into existing demand.
                    native_decrease = (
                        changed == {"picking_id"} and not values["picking_id"]
                        and _trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN)
                        and move.state not in ("done", "cancel") and not move.picked
                        and not move.move_line_ids and move.product_uom.is_zero(move.quantity)
                        and move.product_uom.compare(move.product_uom_qty, 0) < 0
                    )
                    if native_decrease:
                        changed.clear()
                    if changed:
                        raise UserError(_("Campaign delivery mappings cannot be changed directly."))
                    if move.state == "done" and {"quantity", "product_uom_qty", "picked"}.intersection(values):
                        raise UserError(_("Completed campaign dispatch quantities cannot be edited directly."))
            # Only the native quantity/picked inverse of an allocated pool move
            # receives this capability. Caller-supplied relational commands must
            # each pass the raw-line scope and entitlement checks independently.
            native_inverse = validate_preparation and bool(pools) and "move_line_ids" not in values
            writer = self.with_context(_oct_campaign_preparation_token=_PREPARATION_TOKEN) if native_inverse else self
            result = super(StockMove, writer).write(values)
            if validate_preparation:
                self._campaign_assert_preparation_bounds(snapshot)
            if not trusted and (protected.intersection(values) or values.get("state") == "done"):
                if self.filtered(lambda m: m.state == "done")._campaign_linked_orders():
                    raise UserError(_("Completed stock cannot be attached to a campaign order directly."))
            return result

    def unlink(self):
        pools = self._campaign_mutation_pools()
        if not pools:
            return super().unlink()
        with self.env.cr.savepoint():
            pools._campaign_lock()
            if not _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN):
                finals = self.filtered(lambda m: m.location_dest_id.usage == "customer" and m.state != "draft")
                for move in finals:
                    if not move._campaign_linked_orders():
                        continue
                    # Native procurement merges cancel and empty a superseded
                    # move before unlinking it. Only the stock-authorized Sales
                    # lifecycle carries this in-process event capability.
                    merge_cleanup = (
                        _trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN)
                        and move.state == "cancel" and not move.picked
                        and not move.move_line_ids and move.product_uom.is_zero(move.quantity)
                    )
                    if not merge_cleanup:
                        raise UserError(_("Confirmed campaign delivery moves cannot be deleted directly."))
            return super().unlink()


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        with self.env.cr.savepoint():
            self.check_access("write")
            moves = self.move_ids
            pools = self.env["oct.campaign.pool"]._for_moves(moves)
            pools._campaign_lock()
            moves._campaign_assert_dispatch(pools, preflight=True)
            return super().button_validate()

    def _action_done(self):
        with self.env.cr.savepoint():
            return super()._action_done()

    def do_unreserve(self):
        pools = self.env["oct.campaign.pool"]._for_moves(self.move_ids)
        if not pools:
            return super().do_unreserve()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super().do_unreserve()
            pools._campaign_reconcile()
            return result

    def action_cancel(self):
        pools = self.env["oct.campaign.pool"]._for_moves(self.move_ids)
        if not pools:
            return super().action_cancel()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            active = self.move_ids._campaign_linked_orders().filtered(lambda order: order.state == "sale")
            if active and not (_trusted(self.env, "_oct_campaign_event_token", _EVENT_TOKEN)
                               or _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN)):
                raise UserError(_("Cancel an active campaign order through the Sales workflow, preserving its outstanding demand."))
            return super().action_cancel()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def _campaign_effective_line_values(self, values_list):
        defaults = self.default_get([
            "move_id", "quantity", "product_uom_id", "product_id", "company_id",
            "picking_id", "location_id", "location_dest_id", "picked",
        ])
        return [{**defaults, **values} for values in values_list]

    def _campaign_preparation_moves(self, values_list=()):
        moves = self.move_id
        for values in values_list:
            moves |= self.env["stock.move"].browse(values.get("move_id") or [])
        return moves

    def _campaign_assert_line_preparation(self, snapshot):
        finals = self.filtered(lambda ml: ml.location_dest_id.usage == "customer"
                               and ml.location_id.usage != "customer" and ml.quantity > 0
                               and ml.state not in ("done", "cancel"))
        for line in finals:
            if not line._campaign_line_mutation_pools():
                continue
            move = line.move_id
            if (not move or line.product_id != move.product_id or line.company_id != move.company_id
                    or line.location_id != move.location_id or line.location_dest_id != move.location_dest_id):
                raise UserError(_("Campaign preparation requires the allocated move's company, product and locations."))
            # Aggregate all lines of the move, including batch creates and UoM
            # changes; each line must not claim the same entitlement separately.
            quantity = sum(ml.product_uom_id._compute_quantity(ml.quantity, move.product_id.uom_id, round=False)
                           for ml in move.move_line_ids)
            if move.product_id.uom_id.compare(quantity, snapshot.get(move.id, 0)) > 0:
                raise UserError(_("Prepared quantity exceeds this move's allocated stock. Use Check Availability to reconcile campaign priority."))

    def _campaign_protected_lines(self):
        return self.filtered(lambda ml: ml.location_dest_id.usage == "customer"
                             and ml.location_id.usage != "customer"
                             and ml.move_id._campaign_linked_orders())

    def _action_done(self):
        if not _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN):
            finals = self.filtered(lambda ml: ml.location_dest_id.usage == "customer"
                                   and ml.location_id.usage != "customer")
            pools = finals._campaign_line_mutation_pools()
            if finals._campaign_protected_lines() or pools:
                raise UserError(_("Campaign stock lines must complete through the validated stock move workflow."))
        return super()._action_done()

    @api.model_create_multi
    def create(self, vals_list):
        with self.env.cr.savepoint():
            effective = self._campaign_effective_line_values(vals_list)
            pools = self._campaign_line_mutation_pools(effective)
            if pools:
                pools._campaign_lock()
            validate_preparation = not _preparation_trusted(self.env)
            snapshot = self._campaign_preparation_moves(effective)._campaign_preparation_snapshot() if validate_preparation else {}
            lines = super().create(vals_list)
            if validate_preparation:
                lines._campaign_assert_line_preparation(snapshot)
            if not _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN):
                finals = lines.filtered(lambda ml: ml.location_dest_id.usage == "customer"
                                        and ml.location_id.usage != "customer")
                direct_done = finals.filtered(lambda ml: ml.state == "done")
                if direct_done and (direct_done._campaign_protected_lines() or direct_done._campaign_line_mutation_pools()):
                    raise UserError(_("Completed campaign dispatch lines cannot be created directly."))
            return lines

    def write(self, values):
        with self.env.cr.savepoint():
            pools = self._campaign_line_mutation_pools([values])
            if pools:
                pools._campaign_lock()
            preparation_fields = {
                "quantity", "product_uom_id", "picked", "move_id", "picking_id", "product_id",
                "company_id", "location_id", "location_dest_id", "lot_id", "package_id", "owner_id",
            }
            validate_preparation = bool(preparation_fields.intersection(values)) and not _preparation_trusted(self.env)
            snapshot = self._campaign_preparation_moves([values])._campaign_preparation_snapshot() if validate_preparation else {}
            trusted = _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN)
            mapping = {"move_id", "picking_id", "product_id", "company_id", "location_id", "location_dest_id"}
            if not trusted:
                protected = self._campaign_protected_lines()
                finals = self.filtered(lambda ml: ml.location_dest_id.usage == "customer"
                                       and ml.location_id.usage != "customer")
                if values.get("state") == "done" and (protected or finals._campaign_line_mutation_pools()):
                    raise UserError(_("Campaign stock lines must complete through validated dispatch, not direct state edits."))
                for line in protected:
                    if any(name in values and (line[name].id or False) != (values[name] or False) for name in mapping):
                        raise UserError(_("Campaign delivery line mappings cannot be changed directly."))
                if any(line.state == "done" for line in protected) and {
                        "quantity", "product_uom_id", "lot_id", "package_id", "result_package_id", "owner_id", "picked",
                }.intersection(values):
                    raise UserError(_("Completed campaign dispatch lines cannot be edited directly."))
            result = super().write(values)
            if validate_preparation:
                self._campaign_assert_line_preparation(snapshot)
            if not trusted and mapping.intersection(values):
                done = self.filtered(lambda ml: ml.state == "done" and ml.location_dest_id.usage == "customer"
                                     and ml.location_id.usage != "customer")
                if done and (done._campaign_protected_lines() or done._campaign_line_mutation_pools()):
                    raise UserError(_("Completed stock lines cannot be attached to campaign dispatch directly."))
            return result

    def unlink(self):
        pools = self._campaign_line_mutation_pools()
        if not pools:
            return super().unlink()
        with self.env.cr.savepoint():
            pools._campaign_lock()
            if not _trusted(self.env, "_oct_campaign_done_token", _DONE_TOKEN):
                if self.filtered(lambda ml: ml.state == "done")._campaign_protected_lines():
                    raise UserError(_("Completed campaign dispatch lines cannot be deleted directly."))
            return super().unlink()

    def _campaign_line_mutation_pools(self, values_list=()):
        pools = self.move_id._campaign_mutation_pools()
        # Raw line edits can differ from their parent move's source dimensions.
        # Resolve the actual old line scope as well as proposed values.
        for line in self:
            projection = self.env["stock.move"].new({
                "company_id": line.company_id.id, "product_id": line.product_id.id,
                "location_id": line.location_id.id, "location_dest_id": line.location_dest_id.id,
                "sale_line_id": line.move_id.sale_line_id.id,
            })
            pools |= self.env["oct.campaign.pool"]._for_moves(projection)
        for values in values_list:
            moves = self.move_id | self.env["stock.move"].browse(values.get("move_id") or [])
            pools |= moves._campaign_mutation_pools([values])
        return pools.sorted("id")
