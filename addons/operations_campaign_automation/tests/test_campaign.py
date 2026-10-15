"""Bounded synthetic campaign tests; actual execution belongs to the owned runner."""

from datetime import date, timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCampaignAutomation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.warehouse = cls.env["stock.warehouse"].search([
            ("company_id", "=", cls.company.id),
        ], limit=1)
        cls.warehouse.out_type_id.write({
            "reservation_method": "manual", "create_backorder": "always",
        })
        cls.coordinator = cls._user("coordinator", [
            "sales_team.group_sale_salesman_all_leads",
            "operations_dispatch_promise.group_dispatch_coordinator",
        ])
        cls.stock_user = cls._user("warehouse", ["stock.group_stock_user"])
        # Standard purchase_stock cancellation activity logging reads upstream
        # purchase lines. Stock User supplies that native read ACL; keep the
        # Sales-only coordinator and Stock-only dispatcher separate.
        cls.lifecycle_user = cls._user("lifecycle", [
            "sales_team.group_sale_salesman_all_leads", "stock.group_stock_user",
            "operations_dispatch_promise.group_dispatch_coordinator",
        ])
        cls.manager = cls._user("manager", [
            "stock.group_stock_manager",
            "operations_dispatch_promise.group_dispatch_coordinator",
            "operations_control_tower.group_operations_manager",
        ])
        cls.plain_user = cls._user("ordinary", ["base.group_user"])
        cls.portal = cls._user("portal", ["base.group_portal"])
        cls.product, cls.second_product = cls.env["product.product"].create([
            {"name": f"Synthetic Campaign {name}", "type": "consu",
             "is_storable": True, "tracking": "none", "uom_id": cls.unit.id}
            for name in ("Goods", "Second Goods")
        ])
        cls.customer = cls.env["res.partner"].create({
            "name": "Synthetic Campaign Customer", "is_company": False,
        })
        cls.pool = cls.env["oct.campaign.pool"].with_user(cls.manager).create({
            "name": "Synthetic Campaign Pool", "warehouse_id": cls.warehouse.id,
            "location_id": cls.warehouse.lot_stock_id.id,
            "product_ids": [Command.set((cls.product | cls.second_product).ids)],
            "responsible_id": cls.manager.id,
        })

    @classmethod
    def _user(cls, suffix, groups, company=None):
        company = company or cls.company
        return cls.env["res.users"].create({
            "name": f"Synthetic Campaign {suffix}",
            "login": f"synthetic_campaign_{suffix}",
            "company_id": company.id, "company_ids": [Command.set(company.ids)],
            "group_ids": [Command.set([cls.env.ref(g).id for g in groups])],
        })

    def _as(self, records, user=None):
        user = user or self.coordinator
        return records.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids,
        )

    def _order(self, quantity=10, policy="consumer", due="2030-12-15",
               lines=None, campaign=True, confirm=True):
        lines = lines if lines is not None else [(self.product, quantity, self.unit)]
        values = {
            "partner_id": self.customer.id, "user_id": self.coordinator.id,
            "warehouse_id": self.warehouse.id, "picking_policy": "direct",
            "commitment_date": "2030-12-14 12:00:00",
            "order_line": [Command.create({
                "product_id": product.id, "name": product.name,
                "product_uom_qty": qty, "product_uom_id": uom.id,
                "price_unit": 10, "discount": 20, "tax_ids": [Command.clear()],
            }) for product, qty, uom in lines],
        }
        if campaign:
            values.update(oct_campaign_pool_id=self.pool.id, oct_campaign_policy=policy)
        order = self._as(self.env["sale.order"]).create(values)
        if confirm:
            order.action_confirm()
            if campaign and due:
                self._promise(order, due)
        return order

    def _promise(self, order, due):
        model = self._as(self.env["oct.dispatch.promise"])
        return model.browse(model.establish(order.id, due))

    def _proposal(self, order, due):
        promise = self._as(self.env["oct.dispatch.promise"]).search([
            ("order_id", "=", order.id),
        ])
        return self._as(self.env["oct.dispatch.proposal"]).browse(
            promise.propose(due, "Synthetic supplier risk"),
        )

    def _respond(self, proposal, decision):
        return proposal.respond(
            decision, "Synthetic Customer Contact", "email",
            "2030-12-01 10:00:00", "Synthetic manual response TEST-CAMPAIGN",
        )

    def _seed(self, quantity, product=None):
        self.env["stock.quant"]._update_available_quantity(
            product or self.product, self.warehouse.lot_stock_id, quantity,
        )

    def _reconcile(self):
        self.assertFalse(self.pool.env.su)
        self.assertFalse(self.manager.has_group("sales_team.group_sale_salesman"))
        self.pool.action_reconcile()

    def _pickings(self, order):
        return self._as(order.picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel") and p.picking_type_id.code == "outgoing",
        ), self.stock_user)

    def _reserved(self, order, product=None):
        moves = self._pickings(order).move_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
            and (not product or m.product_id == product),
        )
        return sum(m.product_uom._compute_quantity(m.quantity, m.product_id.uom_id)
                   for m in moves)

    def _prepare(self, picking, quantity=None):
        moves = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
        if quantity is not None:
            moves.ensure_one()
            moves.write({"quantity": quantity, "picked": True})
        else:
            for move in moves:
                move.write({"quantity": move.product_uom_qty, "picked": True})

    def _dispatch(self, order, quantity=None):
        picking = self._pickings(order)
        picking.ensure_one()
        self.assertFalse(picking.env.su)
        self._prepare(picking, quantity)
        result = picking.button_validate()
        self.assertNotIsInstance(result, dict, "Unexpected stock validation wizard")
        self.assertEqual(picking.state, "done")
        return picking

    def _reject(self, action, order):
        delivered = order.order_line.mapped("qty_delivered")
        quantities = (self.product.qty_available, self.second_product.qty_available)
        with self.assertRaises(UserError):
            with self.cr.savepoint():
                action()
        self.assertEqual(order.order_line.mapped("qty_delivered"), delivered)
        self.assertEqual((self.product.qty_available, self.second_product.qty_available), quantities)

    def test_reverse_creation_priority_and_repeated_corporate_backorders(self):
        last = self._order(100, "consumer", "2030-12-17")
        corporate = self._order(600, "corporate", "2030-12-16")
        first = self._order(200, "consumer", "2030-12-15")
        self._seed(500)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, corporate, last)], [200, 300, 0])
        self._dispatch(first)
        self._dispatch(corporate, 300)
        self.assertEqual(corporate.order_line.qty_delivered, 300)
        self._seed(400)  # Fixture receipt; real purchase/MRP is covered by the runner.
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (corporate, last)], [300, 100])
        self._dispatch(corporate, 200)
        self._dispatch(corporate, 100)
        self._dispatch(last)
        self.assertEqual([o.order_line.qty_delivered for o in (first, corporate, last)], [200, 600, 100])
        self.assertEqual(self.product.qty_available, 0)
        self.assertFalse(self._pickings(first | corporate | last))

    def test_incomplete_consumer_holds_priority_stock_but_cannot_dispatch(self):
        first = self._order(10, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(4)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, later)], [4, 0])
        self._reject(lambda: self._dispatch(first, 4), first)
        self.assertEqual(first.oct_campaign_status, "waiting_stock")
        self.assertTrue(first.oct_campaign_next_action)

    def test_multiline_consumer_requires_each_product_then_full_success(self):
        order = self._order(lines=[
            (self.product, 3, self.unit), (self.second_product, 2, self.unit),
        ])
        self._seed(3)
        self._seed(1, self.second_product)
        self._reconcile()
        picking = self._pickings(order)

        def partial():
            for move in picking.move_ids:
                move.write({"quantity": 3 if move.product_id == self.product else 1, "picked": True})
            picking.button_validate()

        self._reject(partial, order)
        self._seed(1, self.second_product)
        self._reconcile()
        self._dispatch(order)
        self.assertEqual(order.order_line.mapped("qty_delivered"), [3, 2])

    def test_duplicate_product_lines_cannot_hide_a_short_order_line(self):
        order = self._order(lines=[
            (self.product, 2, self.unit), (self.product, 3, self.unit),
        ])
        self._seed(4)
        self._reconcile()
        picking = self._pickings(order)

        def partial():
            for move in picking.move_ids:
                move.write({"quantity": 2, "picked": True})
            picking.button_validate()

        self._reject(partial, order)
        self._seed(1)
        self._reconcile()
        self._dispatch(order)
        self.assertEqual(order.order_line.mapped("qty_delivered"), [2, 3])

    def test_unpicked_second_product_is_not_complete_dispatch(self):
        order = self._order(lines=[
            (self.product, 2, self.unit), (self.second_product, 3, self.unit),
        ])
        self._seed(2)
        self._seed(3, self.second_product)
        self._reconcile()
        picking = self._pickings(order)

        def omit_second():
            picking.move_ids.filtered(lambda m: m.product_id == self.product).write({"picked": True})
            picking.move_ids.filtered(lambda m: m.product_id == self.second_product).write({"picked": False})
            picking.button_validate()

        self._reject(omit_second, order)

    def test_consumer_uom_conversion_rejects_half_dozen_and_allows_full_dozen(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        order = self._order(lines=[(self.product, 1, dozen)])
        self._seed(12)
        self._reconcile()
        self.assertEqual(self._reserved(order), 12)
        move = self._pickings(order).move_ids
        partial_quantity = self.unit._compute_quantity(6, move.product_uom)
        self._reject(lambda: self._dispatch(order, partial_quantity), order)
        self._dispatch(order)
        self.assertEqual(order.order_line.qty_delivered, 1)
        self.assertEqual(self.product.qty_available, 0)

    def test_missing_promise_has_actionable_block_and_no_fallback_allocation(self):
        order = self._order(due=None)
        self._seed(10)
        self._reconcile()
        self.assertEqual(self._reserved(order), 0)
        self.assertEqual(order.oct_campaign_status, "missing_promise")
        self.assertTrue(order.oct_campaign_next_action)
        self.assertTrue(order.oct_campaign_blocker_id)
        self._reject(lambda: self._dispatch(order), order)
        self._promise(order, "2030-12-15")
        self._reconcile()
        self.assertEqual(self._reserved(order), 10)
        self._dispatch(order)

    def test_unpicked_reservations_reclaimed_but_picked_reservations_preserved(self):
        later = self._order(5, "corporate", "2030-12-20")
        self._seed(5)
        self._reconcile()
        self.assertEqual(self._reserved(later), 5)
        earlier = self._order(5, "consumer", "2030-12-15")
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
        self._pickings(earlier).move_ids.write({"picked": True})
        newest = self._order(5, "corporate", "2030-12-10")
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (newest, earlier, later)], [0, 5, 0])

    def _assert_pool_reservations(self, expected):
        quants = self.env["stock.quant"].search([
            ("company_id", "=", self.company.id), ("product_id", "=", self.product.id),
            ("location_id", "=", self.warehouse.lot_stock_id.id),
        ])
        reserved = sum(quants.mapped("reserved_quantity"))
        self.assertEqual(reserved, expected)
        self.assertLessEqual(reserved, sum(quants.mapped("quantity")))

    def _outside_nested_preparation_fixture(self):
        campaign = self._order(5, "corporate")
        self._seed(5)
        self._reconcile()
        outside_product = self.env["product.product"].create({
            "name": "Synthetic Unconfigured Preparation Product", "type": "consu",
            "is_storable": True, "tracking": "none", "uom_id": self.unit.id,
        })
        outside = self._order(campaign=False, lines=[(outside_product, 1, self.unit)])
        self.env["stock.quant"]._update_available_quantity(outside_product, self.warehouse.lot_stock_id, 1)
        picking = self._pickings(outside)
        picking.action_assign()
        move = picking.move_ids
        # Ordinary quantity inverses outside a campaign pool retain their native path.
        move.write({"quantity": 1, "picked": True})
        self.assertEqual(move.quantity, 1)
        self.assertTrue(move.picked)
        return campaign, move, outside_product

    def _nested_preparation_line(self, move, product):
        return {
            "product_id": product.id, "product_uom_id": self.unit.id, "quantity": 1, "picked": True,
            "company_id": self.company.id, "location_id": self.warehouse.lot_stock_id.id,
            "location_dest_id": move.location_dest_id.id,
        }

    def test_outside_relational_commands_cannot_prepare_or_retarget_campaign_lines(self):
        campaign, outside_move, outside_product = self._outside_nested_preparation_fixture()
        campaign_line = self._pickings(campaign).move_ids.move_line_ids
        commands = (
            Command.create(self._nested_preparation_line(outside_move, self.product)),
            Command.update(campaign_line.id, {"quantity": 6, "picked": True}),
            Command.link(campaign_line.id),
        )
        for command in commands:
            with self.subTest(command=command[0]):
                with self.assertRaises(UserError):
                    outside_move.write({"move_line_ids": [command]})
                self.assertEqual(self._reserved(campaign), 5)
                self._assert_pool_reservations(5)
                self.assertEqual(outside_move.move_line_ids.product_id, outside_product)
                self.assertEqual(outside_move.quantity, 1)
                self.assertEqual(campaign_line.move_id.sale_line_id.order_id, campaign)

    def test_mixed_quantity_and_relational_commands_cannot_mint_preparation_capability(self):
        campaign, outside_move, outside_product = self._outside_nested_preparation_fixture()
        with self.assertRaises(UserError):
            outside_move.with_context(
                _oct_campaign_preparation_token=True, _oct_campaign_done_token=True,
                _oct_campaign_allocation_token=True, _oct_campaign_event_token=True,
            ).write({
                "quantity": 1, "picked": True,
                "move_line_ids": [Command.create(self._nested_preparation_line(outside_move, self.product))],
            })
        self.assertEqual(self._reserved(campaign), 5)
        self._assert_pool_reservations(5)
        self.assertEqual(outside_move.move_line_ids.product_id, outside_product)
        self.assertEqual(outside_move.quantity, 1)

    def test_campaign_parent_relational_cross_product_cannot_bypass_raw_line_guard(self):
        order = self._order(5, "corporate")
        self._seed(5)
        self._seed(1, self.second_product)
        self._reconcile()
        move = self._pickings(order).move_ids
        with self.assertRaises(UserError):
            move.write({
                "quantity": 5, "picked": True,
                "move_line_ids": [Command.create(self._nested_preparation_line(move, self.second_product))],
            })
        self.assertEqual(move.move_line_ids.product_id, self.product)
        self.assertEqual(self._reserved(order), 5)
        self._assert_pool_reservations(5)
        second_quants = self.env["stock.quant"].search([
            ("company_id", "=", self.company.id), ("product_id", "=", self.second_product.id),
            ("location_id", "=", self.warehouse.lot_stock_id.id),
        ])
        self.assertEqual(sum(second_quants.mapped("reserved_quantity")), 0)
        # The same actor's normal within-entitlement inverse remains supported.
        move.write({"quantity": 4, "picked": True})
        self.assertEqual(self._reserved(order), 4)
        self._assert_pool_reservations(4)

    def test_saved_manual_preparation_cannot_claim_later_order_allocation(self):
        earlier = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        move = self._pickings(later).move_ids
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
        self.assertFalse(move.env.su)
        with self.assertRaisesRegex(UserError, "Check Availability"):
            move.with_context(
                _oct_campaign_preparation_token=True, _oct_campaign_allocation_token=True,
                _oct_campaign_done_token=True,
            ).write({"quantity": 5, "picked": True})
        # Inspect the saved preparation immediately, without wrapping dispatch.
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
        self.assertFalse(move.picked)
        self._assert_pool_reservations(5)
        values = {
            "product_id": self.product.id,
            "product_uom": self.unit.id, "product_uom_qty": 5,
            "location_id": self.warehouse.lot_stock_id.id,
            "location_dest_id": move.location_dest_id.id,
            "company_id": self.company.id, "picking_id": move.picking_id.id,
            "sale_line_id": later.order_line.id,
        }
        with self.assertRaisesRegex(UserError, "Check Availability"):
            self._as(self.env["stock.move"], self.stock_user).with_context(default_quantity=5).create(values)
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
        self._assert_pool_reservations(5)

    def test_raw_line_saved_preparation_defaults_batches_and_uom_cannot_increase_entitlement(self):
        earlier = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(6)
        self._reconcile()
        move = self._pickings(later).move_ids
        line = move.move_line_ids
        line.ensure_one()
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 1])
        dozen = self.env.ref("uom.product_uom_dozen")
        for values in ({"quantity": 5, "picked": True}, {"product_uom_id": dozen.id}):
            with self.subTest(values=values):
                with self.assertRaisesRegex(UserError, "Check Availability"):
                    line.write(values)
                self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 1])
                self._assert_pool_reservations(6)
        values = {
            "move_id": move.id, "product_id": self.product.id, "product_uom_id": self.unit.id,
            "quantity": 1, "location_id": self.warehouse.lot_stock_id.id,
            "location_dest_id": move.location_dest_id.id, "company_id": self.company.id,
        }
        model = self._as(self.env["stock.move.line"], self.stock_user)
        with self.assertRaisesRegex(UserError, "Check Availability"):
            model.create([values, values])
        defaults = {f"default_{name}": value for name, value in values.items()}
        defaults["default_quantity"] = 5
        defaults["_oct_campaign_preparation_token"] = True
        with self.assertRaisesRegex(UserError, "Check Availability"):
            model.with_context(**defaults).create({})
        standalone = {key: value for key, value in values.items() if key != "move_id"}
        with self.assertRaises(UserError):
            model.create(standalone)
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 1])
        self._assert_pool_reservations(6)

    def test_public_unreserve_restores_earlier_priority_and_saved_partial_remains_valid(self):
        earlier = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        self._pickings(earlier).do_unreserve()
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
        with self.assertRaisesRegex(UserError, "Check Availability"):
            self._pickings(later).move_ids.write({"quantity": 5, "picked": True})
        self._assert_pool_reservations(5)
        self._dispatch(earlier)
        self._seed(3)
        self._reconcile()
        picking = self._pickings(later)
        picking.move_ids.write({"quantity": 2, "picked": True})
        self.assertEqual(self._reserved(later), 2)
        self._assert_pool_reservations(2)
        result = picking.button_validate()
        self.assertNotIsInstance(result, dict)
        self.assertEqual(later.order_line.qty_delivered, 2)
        self.assertEqual(later.order_line.product_uom_qty - later.order_line.qty_delivered, 3)
        self.assertEqual(self._reserved(later), 1)
        self._assert_pool_reservations(1)

    def test_campaign_delivery_cancel_and_demand_edits_require_sales_lifecycle(self):
        earlier = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        picking = self._pickings(earlier)
        move = picking.move_ids
        for action in (
            picking.action_cancel,
            lambda: move.write({"state": "cancel"}),
            lambda: move.write({"product_uom_qty": 10}),
            lambda: move.write({"product_uom": self.env.ref("uom.product_uom_dozen").id}),
        ):
            with self.assertRaises(UserError):
                action()
            self.assertEqual(earlier.state, "sale")
            self.assertEqual([self._reserved(o) for o in (earlier, later)], [5, 0])
            self._assert_pool_reservations(5)
        self._as(earlier, self.lifecycle_user).with_context(disable_cancel_warning=True).action_cancel()
        self.assertEqual(earlier.state, "cancel")
        self.assertEqual([self._reserved(o) for o in (earlier, later)], [0, 5])
        self._assert_pool_reservations(5)

    def test_reserved_outside_move_cannot_be_retargeted_to_campaign_demand(self):
        self.pool.product_ids = [Command.set(self.second_product.ids)]
        outside = self._order(5, campaign=False)
        self._seed(5)
        self._pickings(outside).action_assign()
        self.assertEqual(self._reserved(outside), 5)
        self.pool.product_ids = [Command.set((self.product | self.second_product).ids)]
        campaign = self._order(5)
        move = self._pickings(outside).move_ids
        original_line = move.sale_line_id
        with self.assertRaises(UserError):
            move.write({"sale_line_id": campaign.order_line.id})
        self.assertEqual(move.sale_line_id, original_line)
        self.assertEqual([self._reserved(o) for o in (outside, campaign)], [5, 0])
        self._assert_pool_reservations(5)

    def test_partly_prepared_consumer_requires_unprepare_then_check_availability_to_extend(self):
        order = self._order(5, "consumer")
        self._seed(2)
        self._reconcile()
        picking = self._pickings(order)
        move = picking.move_ids
        move.write({"quantity": 2, "picked": True})
        self._seed(3)
        self._reconcile()
        self.assertTrue(move.picked)
        self.assertEqual(self._reserved(order), 2)
        with self.assertRaisesRegex(UserError, "Check Availability"):
            move.write({"quantity": 5, "picked": True})
        self._assert_pool_reservations(2)
        # The supported whole-move preparation policy preserves prepared stock;
        # a warehouse operator explicitly unprepares before extending allocation.
        move.write({"picked": False})
        picking.action_assign()
        self.assertEqual(self._reserved(order), 5)
        self._assert_pool_reservations(5)
        self._dispatch(order)
        self.assertEqual(order.order_line.qty_delivered, 5)

    def test_pending_rejected_stale_dates_do_not_reprioritize_acceptance_does(self):
        early = self._order(5, "corporate", "2030-12-15")
        late = self._order(5, "consumer", "2030-12-20")
        self._seed(5)
        self._reconcile()
        rejected = self._proposal(late, "2030-12-10")
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (early, late)], [5, 0])
        self.assertTrue(self._respond(rejected, "rejected"))
        stale = self._proposal(late, "2030-12-09")
        late.order_line.product_uom_qty = 6
        self.assertFalse(self._respond(stale, "accepted"))
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (early, late)], [5, 0])
        accepted = self._proposal(late, "2030-12-10")
        self.assertTrue(self._respond(accepted, "accepted"))
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (early, late)], [0, 5])
        self.assertEqual(accepted.promise_id.current_date, date(2030, 12, 10))

    def test_reconciliation_and_blocker_creation_are_idempotent(self):
        order = self._order(10)
        self._seed(4)
        self._reconcile()
        blocker = order.oct_campaign_blocker_id
        self.assertTrue(blocker)
        before = [self._reserved(order), blocker.id,
                  self.env["operations.control.item"].search_count([])]
        self._reconcile()
        self._reconcile()
        self.assertEqual([self._reserved(order), order.oct_campaign_blocker_id.id,
                          self.env["operations.control.item"].search_count([])], before)
        self.assertTrue(blocker.owner_id)
        self.assertTrue(blocker.next_action)

    def test_native_confirmed_quantity_decrease_releases_stock_and_stales_proposal(self):
        first = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, later)], [5, 0])
        proposal = self._proposal(first, "2030-12-14")
        confirmed_at = first.oct_campaign_confirmed_at

        # Exercise the normal Sales procurement delta, not direct stock edits.
        first.order_line.write({"product_uom_qty": 4})
        self.assertEqual([self._reserved(o) for o in (first, later)], [4, 1])
        self.assertEqual(first.order_line.product_uom_qty - first.order_line.qty_delivered, 4)
        self.assertTrue(proposal.is_stale)
        self.assertFalse(self._respond(proposal, "accepted"))
        self.assertFalse(self._respond(proposal, "accepted"))
        self.assertEqual(proposal.state, "stale")
        self.assertFalse(proposal.applied)
        self.assertEqual(proposal.promise_id.current_date, date(2030, 12, 15))
        self.assertEqual(first.oct_campaign_confirmed_at, confirmed_at)
        self._reconcile()
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, later)], [4, 1])
        self.assertFalse(first.order_line.move_ids.filtered(
            lambda move: move.state not in ("done", "cancel") and move.product_uom_qty < 0,
        ))
        self._dispatch(first)
        self.assertEqual(first.order_line.qty_delivered, 4)
        self.assertEqual(self.product.qty_available, 1)

    def test_native_zero_quantity_releases_all_stock_and_restoration_keeps_original_priority(self):
        first = self._order(5, "consumer", "2030-12-15")
        later = self._order(5, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        proposal = self._proposal(first, "2030-12-14")
        confirmed_at = first.oct_campaign_confirmed_at

        first.order_line.write({"product_uom_qty": 0})
        self.assertEqual(first.order_line.qty_delivered, 0)
        self.assertEqual([self._reserved(o) for o in (first, later)], [0, 5])
        self.assertFalse(self._pickings(first))
        self.assertTrue(proposal.is_stale)
        self.assertFalse(self._respond(proposal, "accepted"))
        self.assertFalse(self._respond(proposal, "accepted"))
        self.assertEqual(proposal.promise_id.current_date, date(2030, 12, 15))
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, later)], [0, 5])
        self.assertEqual(self.product.qty_available, 5)

        first.order_line.write({"product_uom_qty": 5})
        self.assertEqual(first.oct_campaign_confirmed_at, confirmed_at)
        self.assertEqual(len(first.oct_campaign_confirmation_ids), 1)
        self.assertEqual([self._reserved(o) for o in (first, later)], [5, 0])
        self.assertFalse(self._respond(proposal, "accepted"))
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, later)], [5, 0])
        self.assertFalse(proposal.applied)

    def test_consumer_backorder_never_and_context_flags_cannot_cancel_balance(self):
        order = self._order(10)
        self._seed(5)
        self._reconcile()
        picking = self._pickings(order)
        self._as(self.warehouse.out_type_id, self.manager).create_backorder = "never"

        def attempt():
            self._prepare(picking, 5)
            picking.with_context(
                skip_backorder=True, skip_immediate=True, skip_sanity_check=True,
                cancel_backorder=True, oct_campaign_internal=True,
                bypass_campaign_guard=True,
            ).button_validate()

        self._reject(attempt, order)

        self.assertEqual(order.order_line.product_uom_qty, 10)
        self.assertTrue(self._pickings(order))

    def test_corporate_partial_never_context_and_raw_cancel_cannot_erase_balance(self):
        order = self._order(5, "corporate")
        self._seed(3)
        self._reconcile()
        picking = self._pickings(order)
        move = picking.move_ids

        def attempt(mode):
            self._prepare(picking, 3)
            if mode == "never":
                self._as(self.warehouse.out_type_id, self.manager).create_backorder = "never"
                picking.button_validate()
            elif mode == "context":
                picking.with_context(cancel_backorder=True, skip_backorder=True).button_validate()
            else:
                move._action_done(cancel_backorder=True)

        for mode in ("never", "context", "raw"):
            with self.subTest(mode=mode):
                self._reject(lambda: attempt(mode), order)
                self.assertEqual(order.order_line.product_uom_qty, 5)
                self.assertEqual(order.order_line.qty_delivered, 0)
                self.assertEqual(move.product_uom_qty, 5)
                self.assertNotIn(move.state, ("done", "cancel"))
                self.assertEqual(self._reserved(order), 3)
                self.assertEqual(self.product.qty_available, 3)

        # An explicit Sales cancellation remains distinct from discarding the
        # remaining demand while claiming a successful partial dispatch.
        self._as(order, self.lifecycle_user).with_context(disable_cancel_warning=True).action_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertEqual(self._reserved(order), 0)
        self.assertEqual(order.order_line.qty_delivered, 0)
        self.assertEqual(self.product.qty_available, 3)
        self.assertEqual(order.order_line.product_uom_qty, 5)
        self.assertFalse(self._pickings(order))

    def test_consumer_direct_move_and_raw_line_done_paths_are_guarded(self):
        order = self._order(10)
        self._seed(5)
        self._reconcile()
        picking = self._pickings(order)
        move = picking.move_ids
        for path in ("move", "raw_line", "move_state", "line_state", "create_done"):
            with self.subTest(path=path):
                def attempt():
                    self._prepare(picking, 5)
                    if path == "move":
                        move._action_done(cancel_backorder=True)
                    elif path == "raw_line":
                        move.move_line_ids._action_done()
                    elif path == "move_state":
                        move.write({"state": "done"})
                    elif path == "line_state":
                        move.move_line_ids.write({"state": "done"})
                    else:
                        move.copy({"state": "done"})
                self._reject(attempt, order)

    def test_campaign_move_mapping_cannot_be_removed_or_retargeted(self):
        order = self._order(10)
        self._seed(5)
        self._reconcile()
        move = self._pickings(order).move_ids
        for values in (
            {"sale_line_id": False}, {"picking_id": False},
            {"product_id": self.second_product.id},
            {"location_id": self.env.ref("stock.stock_location_customers").id},
        ):
            with self.subTest(values=values):
                self._reject(lambda: move.write(values), order)
        self.assertEqual(move.sale_line_id, order.order_line)

    def test_consumer_split_pickings_cannot_be_aggregated_as_one_dispatch(self):
        order = self._order(lines=[
            (self.product, 2, self.unit), (self.second_product, 3, self.unit),
        ])
        self._seed(2)
        self._seed(3, self.second_product)
        self._reconcile()
        picking = self._pickings(order)

        def split_dispatch():
            split = picking.copy({"move_ids": [Command.clear()]})
            picking.move_ids.filtered(lambda m: m.product_id == self.second_product).write({
                "picking_id": split.id,
            })
            self._prepare(picking)
            self._prepare(split)
            (picking | split).button_validate()

        self._reject(split_dispatch, order)

    def test_mixed_order_picking_cannot_hide_consumer_balance(self):
        consumer = self._order(4, "consumer", "2030-12-15")
        corporate = self._order(4, "corporate", "2030-12-16")
        self._seed(6)
        self._reconcile()
        first, second = self._pickings(consumer), self._pickings(corporate)

        def mixed_dispatch():
            first.move_ids.write({"picking_id": second.id})
            self._prepare(second)
            second.button_validate()

        self._reject(mixed_dispatch, consumer | corporate)

    def test_corporate_forced_quantity_cannot_produce_negative_stock(self):
        order = self._order(5, "corporate")
        self._seed(3)
        self._reconcile()
        self._reject(lambda: self._dispatch(order, 5), order)
        self.assertEqual(self.product.qty_available, 3)

    def test_physical_stock_loss_after_valid_saved_preparation_still_blocks_dispatch(self):
        order = self._order(5, "corporate")
        self._seed(5)
        self._reconcile()
        picking = self._pickings(order)
        self._prepare(picking, 5)
        self.assertTrue(picking.move_ids.picked)
        self._assert_pool_reservations(5)
        # Controlled inventory drift after legitimate preparation: exercise the
        # final physical-stock guard independently of the new entitlement gate.
        self._seed(-2)
        self._reject(picking.button_validate, order)
        self.assertEqual(order.order_line.qty_delivered, 0)
        self.assertEqual(self.product.qty_available, 3)
        self.assertTrue(picking.move_ids.picked)
        self.assertEqual(picking.move_ids.quantity, 5)
        self.assertNotIn(picking.state, ("done", "cancel"))

    def test_batch_physical_stock_loss_after_valid_preparation_blocks_combined_dispatch(self):
        first = self._order(3, "corporate", "2030-12-15")
        second = self._order(3, "corporate", "2030-12-16")
        self._seed(6)
        self._reconcile()
        pickings = self._pickings(first | second)
        for picking in pickings:
            self._prepare(picking, 3)
        self.assertEqual([self._reserved(o) for o in (first, second)], [3, 3])
        self._assert_pool_reservations(6)
        self._seed(-1)  # Deliberate external stock drift after valid saved preparation.
        self._reject(lambda: pickings.move_ids._action_done(), first | second)
        self.assertEqual(first.order_line.qty_delivered, 0)
        self.assertEqual(second.order_line.qty_delivered, 0)
        self.assertEqual(self.product.qty_available, 5)
        self.assertTrue(all(pickings.move_ids.mapped("picked")))

    def test_forced_campaign_reservation_cannot_bypass_pool_reconciliation(self):
        order = self._order(5, "corporate")
        self._seed(3)
        self._reconcile()
        move = self._pickings(order).move_ids
        self._reject(lambda: move.with_context(
            oct_campaign_internal=True, bypass_campaign_guard=True,
        )._action_assign(force_qty=5), order)
        self.assertEqual(self._reserved(order), 3)

    def test_combined_corporate_dispatch_cannot_double_spend_source_stock(self):
        first = self._order(3, "corporate", "2030-12-15")
        second = self._order(3, "corporate", "2030-12-16")
        self._seed(5)
        self._reconcile()
        pickings = self._pickings(first | second)

        def force_both():
            for picking in pickings:
                self._prepare(picking, 3)
            pickings.move_ids._action_done()

        self._reject(force_both, first | second)
        self.assertEqual(self.product.qty_available, 5)

    def test_outside_fully_reserved_claims_are_preserved(self):
        self.pool.product_ids = [Command.set(self.second_product.ids)]
        outside = self._order(5, campaign=False)
        self._seed(5)
        outside_picking = self._pickings(outside)
        outside_picking.action_assign()
        self.assertEqual(self._reserved(outside), 5)
        self.pool.product_ids = [Command.set((self.product | self.second_product).ids)]
        campaign = self._order(5)
        self._reconcile()
        self.assertEqual(self._reserved(outside), 5)
        self.assertEqual(self._reserved(campaign), 0)

    def test_unmanaged_uncovered_competition_is_explicitly_rejected(self):
        self.pool.product_ids = [Command.set(self.second_product.ids)]
        outside = self._order(5, campaign=False)
        self.pool.product_ids = [Command.set((self.product | self.second_product).ids)]
        with self.assertRaises(UserError):
            with self.cr.savepoint():
                self.pool.action_reconcile()
        self.assertEqual(self._reserved(outside), 0)

    def test_frozen_policy_pool_and_confirmation_history_are_server_protected(self):
        order = self._order()
        confirmed_at = order.oct_campaign_confirmed_at
        history = order.oct_campaign_confirmation_ids
        self.assertTrue(confirmed_at)
        self.assertEqual(len(history), 1)
        self.assertEqual(history.confirmed_at, confirmed_at)
        self.assertEqual(history.actor_id, self.coordinator)
        for values in (
            {"oct_campaign_policy": "corporate"}, {"oct_campaign_policy": False},
            {"oct_campaign_pool_id": False},
        ):
            with self.assertRaises(UserError):
                with self.cr.savepoint():
                    order.with_context(oct_campaign_internal=True).write(values)
        for action in (
            lambda: order.write({"oct_campaign_confirmed_at": "2000-01-01 00:00:00"}),
            lambda: history.write({"confirmed_at": "2000-01-01 00:00:00"}),
            lambda: history.unlink(),
            lambda: self._as(self.env["oct.campaign.confirmation"]).create({
                "order_id": order.id, "confirmed_at": confirmed_at,
                "sequence_no": 99, "actor_id": self.coordinator.id,
            }),
        ):
            with self.assertRaises(AccessError):
                with self.cr.savepoint():
                    action()
        self.assertEqual(order.oct_campaign_confirmed_at, confirmed_at)
        self.assertEqual(order.oct_campaign_confirmation_ids, history)
        for values in (
            {"product_ids": [Command.set(self.product.ids)]}, {"active": False},
        ):
            with self.assertRaises(UserError):
                with self.cr.savepoint():
                    self.pool.write(values)

    def test_confirmation_timestamp_not_mutable_date_order_controls_equal_promises(self):
        first = self._order(5, "corporate")
        second = self._order(5, "consumer")
        self.assertLessEqual(first.oct_campaign_confirmed_at, second.oct_campaign_confirmed_at)
        second.date_order = first.date_order - timedelta(days=10)
        self._seed(5)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, second)], [5, 0])

    def test_exact_timestamp_tie_uses_stable_order_id(self):
        fixed = fields.Datetime.to_datetime("2030-12-01 10:00:00")
        first = self._order(5, "consumer", confirm=False)
        second = self._order(5, "corporate", confirm=False)
        with patch.object(fields.Datetime, "now", return_value=fixed):
            second.action_confirm()
            first.action_confirm()
        self._promise(second, "2030-12-15")
        self._promise(first, "2030-12-15")
        self.assertEqual(first.oct_campaign_confirmed_at, second.oct_campaign_confirmed_at)
        self.assertLess(first.id, second.id)
        self._seed(5)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, second)], [5, 0])

    def test_cancel_reconfirm_gets_new_confirmation_and_preserves_history(self):
        first = self._order(5, "consumer")
        second = self._order(5, "corporate")
        old_at = first.oct_campaign_confirmed_at
        history = first.oct_campaign_confirmation_ids
        first.with_context(disable_cancel_warning=True).action_cancel()
        first.action_draft()
        with patch.object(fields.Datetime, "now", return_value=old_at + timedelta(days=1)):
            first.action_confirm()
        self.assertGreater(first.oct_campaign_confirmed_at, old_at)
        self.assertEqual(len(first.oct_campaign_confirmation_ids), 2)
        self.assertIn(history, first.oct_campaign_confirmation_ids)
        self.assertEqual(history.confirmed_at, old_at)
        self._seed(5)
        self._reconcile()
        self.assertEqual([self._reserved(o) for o in (first, second)], [0, 5])

    def test_manual_assignment_expands_to_earlier_competing_orders(self):
        late = self._order(5, "corporate", "2030-12-20")
        early = self._order(5, "consumer", "2030-12-15")
        self._seed(5)
        late_picking = self._pickings(late)
        self.assertFalse(late_picking.env.su)
        self.assertFalse(self.stock_user.has_group("sales_team.group_sale_salesman"))
        late_picking.action_assign()
        self.assertEqual([self._reserved(o) for o in (early, late)], [5, 0])

    def test_recorded_receipt_automatically_assigns_by_campaign_priority(self):
        late = self._order(5, "corporate", "2030-12-20")
        early = self._order(5, "consumer", "2030-12-15")
        incoming = self.warehouse.in_type_id
        receipt = self._as(self.env["stock.picking"], self.stock_user).create({
            "picking_type_id": incoming.id,
            "location_id": incoming.default_location_src_id.id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
            "move_ids": [Command.create({
                "product_id": self.product.id, "product_uom_qty": 5,
                "product_uom": self.unit.id,
                "location_id": incoming.default_location_src_id.id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            })],
        })
        receipt.action_confirm()
        receipt.move_ids.write({"quantity": 5, "picked": True})
        result = receipt.button_validate()
        self.assertNotIsInstance(result, dict)
        self.assertEqual(receipt.state, "done")
        self.assertEqual([self._reserved(o) for o in (early, late)], [5, 0])

    def test_explicit_policy_is_not_inferred_from_customer_entity_type(self):
        self.assertFalse(self.customer.is_company)
        corporate = self._order(5, "corporate")
        self._seed(2)
        self._reconcile()
        self._dispatch(corporate, 2)
        self.assertEqual(corporate.order_line.qty_delivered, 2)
        self.customer.is_company = True
        consumer = self._order(5, "consumer")
        self._seed(2)
        self._reconcile()
        self._reject(lambda: self._dispatch(consumer, 2), consumer)
        with self.assertRaises(UserError):
            with self.cr.savepoint():
                self._order(policy=False)

    def test_public_pool_actions_do_not_grant_stock_privileges_to_sales(self):
        for user in (self.coordinator, self.stock_user, self.plain_user, self.portal):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    with self.cr.savepoint():
                        self._as(self.pool, user).action_reconcile()
        with self.assertRaises(AccessError):
            with self.cr.savepoint():
                self._as(self.env["oct.campaign.pool"], self.coordinator).create({
                    "name": "Unauthorized pool", "warehouse_id": self.warehouse.id,
                    "location_id": self.warehouse.lot_stock_id.id,
                    "product_ids": [Command.set(self.product.ids)],
                    "responsible_id": self.coordinator.id,
                })
        order = self._order()
        for values in (
            {"oct_campaign_status": "ready"},
            {"oct_campaign_next_action": "Bypassed"},
            {"oct_campaign_blocker_id": False},
        ):
            with self.assertRaises(AccessError):
                with self.cr.savepoint():
                    order.with_context(oct_campaign_internal=True).write(values)

    def test_company_pool_is_not_visible_or_mutable_from_other_company(self):
        company = self.env["res.company"].create({"name": "Synthetic Campaign Other Company"})
        foreign_manager = self._user("foreign_manager", [
            "stock.group_stock_manager",
            "operations_dispatch_promise.group_dispatch_coordinator",
        ], company=company)
        warehouse = self.env["stock.warehouse"].search([
            ("company_id", "=", company.id),
        ], limit=1)
        if not warehouse:
            warehouse = self.env["stock.warehouse"].create({
                "name": "Synthetic Campaign Other Warehouse", "code": "SCOT",
                "company_id": company.id,
            })
        foreign_pool = self._as(self.env["oct.campaign.pool"], foreign_manager).create({
            "name": "Synthetic Other Pool", "warehouse_id": warehouse.id,
            "location_id": warehouse.lot_stock_id.id,
            "product_ids": [Command.set(self.product.ids)],
            "responsible_id": foreign_manager.id,
        })
        self.assertFalse(self._as(self.env["oct.campaign.pool"], self.manager).search([
            ("id", "=", foreign_pool.id),
        ]))
        with self.assertRaises(AccessError):
            self._as(foreign_pool, self.manager).action_reconcile()
        with self.assertRaises(AccessError):
            self._as(self.pool, foreign_manager).read(["name"])

    def test_noncampaign_product_keeps_standard_partial_dispatch(self):
        product = self.env["product.product"].create({
            "name": "Synthetic Outside Product", "type": "consu",
            "is_storable": True, "tracking": "none", "uom_id": self.unit.id,
        })
        order = self._order(lines=[(product, 5, self.unit)], campaign=False)
        self._seed(2, product)
        self._pickings(order).action_assign()
        self._dispatch(order, 2)
        self.assertEqual(order.order_line.qty_delivered, 2)
        self.assertEqual(order.oct_campaign_status, "outside")

    def test_policy_without_pool_is_rejected_on_create_and_write(self):
        model = self._as(self.env["sale.order"])
        before = model.search_count([])
        for policy in ("consumer", "corporate"):
            with self.subTest(policy=policy):
                with self.assertRaises(UserError):
                    with self.cr.savepoint():
                        model.create({"partner_id": self.customer.id, "warehouse_id": self.warehouse.id,
                                      "oct_campaign_policy": policy})
        self.assertEqual(model.search_count([]), before)
        outside = self._order(campaign=False, confirm=False)
        with self.assertRaises(UserError):
            with self.cr.savepoint():
                outside.write({"oct_campaign_policy": "consumer"})
        self.assertFalse(outside.oct_campaign_pool_id)
        self.assertFalse(outside.oct_campaign_policy)
        self.assertEqual(outside.oct_campaign_status, "outside")
        outside.write({"client_order_ref": "Synthetic ordinary quotation"})
        self.assertEqual(outside.client_order_ref, "Synthetic ordinary quotation")

    def test_context_defaults_require_both_campaign_configuration_fields(self):
        model = self._as(self.env["sale.order"])
        for defaults in (
            {"default_oct_campaign_policy": "consumer"},
            {"default_oct_campaign_pool_id": self.pool.id},
        ):
            with self.subTest(defaults=defaults):
                with self.assertRaises(UserError):
                    with self.cr.savepoint():
                        model.with_context(**defaults).create({
                            "partner_id": self.customer.id, "warehouse_id": self.warehouse.id,
                        })

    def test_context_campaign_defaults_are_locked_and_validate_goods(self):
        model = self._as(self.env["sale.order"]).with_context(
            default_oct_campaign_pool_id=self.pool.id, default_oct_campaign_policy="consumer",
        )
        values = {
            "partner_id": self.customer.id, "warehouse_id": self.warehouse.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "product_uom_qty": 2,
                "product_uom_id": self.unit.id, "price_unit": 10,
            })],
        }
        revision = self.pool.revision
        quotation = model.create(values)
        self.assertEqual(quotation.oct_campaign_pool_id.id, self.pool.id)
        self.assertEqual(quotation.oct_campaign_policy, "consumer")
        self.assertEqual(quotation.oct_campaign_status, "draft")
        self.assertGreater(self.pool.revision, revision)
        outside_product = self.env["product.product"].create({
            "name": "Synthetic Context Outside Product", "type": "consu",
            "is_storable": True, "tracking": "none", "uom_id": self.unit.id,
        })
        with self.assertRaises(UserError):
            with self.cr.savepoint():
                model.create({
                    "partner_id": self.customer.id, "warehouse_id": self.warehouse.id,
                    "order_line": [Command.create({
                        "product_id": outside_product.id, "product_uom_qty": 1,
                        "product_uom_id": self.unit.id, "price_unit": 10,
                    })],
                })
        ordinary = model.create({**values, "oct_campaign_pool_id": False, "oct_campaign_policy": False})
        self.assertFalse(ordinary.oct_campaign_pool_id)
        self.assertFalse(ordinary.oct_campaign_policy)
        self.assertEqual(ordinary.oct_campaign_status, "outside")

    def test_quotation_pool_and_policy_must_be_removed_together(self):
        quotation = self._order(confirm=False)
        for values in ({"oct_campaign_pool_id": False}, {"oct_campaign_policy": False}):
            with self.subTest(values=values):
                with self.assertRaises(UserError):
                    with self.cr.savepoint():
                        quotation.write(values)
                self.assertEqual(quotation.oct_campaign_pool_id.id, self.pool.id)
                self.assertEqual(quotation.oct_campaign_policy, "consumer")
        quotation.write({"oct_campaign_pool_id": False, "oct_campaign_policy": False})
        self.assertFalse(quotation.oct_campaign_pool_id)
        self.assertFalse(quotation.oct_campaign_policy)
        self.assertEqual(quotation.oct_campaign_status, "outside")
        self.assertFalse(quotation.oct_campaign_next_action)

    def test_raw_line_state_cannot_bypass_guards_with_forged_capability_context(self):
        order = self._order(10)
        self._seed(5)
        self._reconcile()
        picking = self._pickings(order)
        for forged in (True, "_DONE_TOKEN"):
            with self.subTest(forged=forged):
                def attempt():
                    self._prepare(picking, 5)
                    lines = picking.move_line_ids.with_context(
                        _oct_campaign_done_token=forged, _oct_campaign_event_token=forged,
                        _oct_campaign_allocation_token=forged,
                        skip_sanity_check=True, skip_backorder=True, cancel_backorder=True,
                    )
                    lines.write({"state": "done"})
                self._reject(attempt, order)
                self.assertNotEqual(picking.move_ids.state, "done")
                self.assertNotEqual(picking.move_line_ids.state, "done")

    def test_completed_consumer_customer_return_remains_standard_inbound_flow(self):
        order = self._order(5)
        self._seed(5)
        self._reconcile()
        completed = self._dispatch(order)
        customer_location = self.env.ref("stock.stock_location_customers")
        returned = self._as(self.env["stock.picking"], self.stock_user).create({
            "picking_type_id": self.warehouse.in_type_id.id,
            "location_id": customer_location.id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
            "move_ids": [Command.create({
                "product_id": self.product.id, "product_uom_qty": 1,
                "product_uom": self.unit.id, "location_id": customer_location.id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "origin_returned_move_id": completed.move_ids.id,
                "sale_line_id": order.order_line.id,
            })],
        })
        returned.action_confirm()
        returned.move_ids.write({"quantity": 1, "picked": True})
        result = returned.button_validate()
        self.assertNotIsInstance(result, dict)
        self.assertEqual(returned.state, "done")
        self.assertEqual(self.product.qty_available, 1)

    def test_reconciliation_status_failure_rolls_back_reservations_together(self):
        order = self._order(5)
        self._seed(5)
        before = self._reserved(order)

        def fail_status(records):
            raise RuntimeError("Synthetic campaign status failure")

        with patch.object(type(order), "_campaign_sync_status", fail_status):
            with self.assertRaisesRegex(RuntimeError, "Synthetic campaign status failure"):
                self.pool.action_reconcile()
        self.assertEqual(self._reserved(order), before)
        self.assertEqual(order.order_line.qty_delivered, 0)
        self.assertEqual(self.product.qty_available, 5)
        self._reconcile()
        self.assertEqual(self._reserved(order), 5)
