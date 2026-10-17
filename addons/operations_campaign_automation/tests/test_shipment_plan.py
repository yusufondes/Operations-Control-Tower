from datetime import date
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged

from .test_campaign import CampaignCase


@tagged("post_install", "-at_install")
class TestShipmentPlans(CampaignCase):
    def _plan(self, order, quantities=(100, 500), dates=("2030-12-14", "2030-12-18"), approve=False):
        model = self._as(self.env["oct.shipment.plan"])
        plan = model.browse(model.propose(order.id, [
            {"batch": i + 1, "line_id": order.order_line.id, "quantity": qty, "latest_date": dates[i]}
            for i, qty in enumerate(quantities)], "Synthetic split offer"))
        if approve:
            self._answer(plan)
        return plan

    def _answer(self, plan, decision="accepted"):
        return plan.respond(decision, "Synthetic Contact", "email", fields.Datetime.now(), "Synthetic customer response")

    def _send(self, order, qty):
        picking = self._pickings(order)
        self._prepare(picking, qty)
        result = picking.button_validate()
        self.assertNotIsInstance(result, dict)
        self.assertEqual(picking.state, "done")
        return picking

    def test_partial_without_customer_plan_is_blocked_but_full_original_is_allowed(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self._reconcile()
        self._reject(lambda: self._send(order, 100), order)
        self._send(order, 600)
        self.assertEqual(order.order_line.qty_delivered, 600)

    def test_pending_and_rejected_are_not_partial_approval(self):
        order = self._order(600, "corporate")
        self._seed(600)
        plan = self._plan(order)
        self._reject(lambda: self._send(order, 100), order)
        self._answer(plan, "rejected")
        self._reject(lambda: self._send(order, 100), order)
        self.assertFalse(order._shipment_current_plan())

    def test_early_exact_batches_preserve_backorder_and_history(self):
        order = self._order(600, "corporate")
        self._seed(600)
        plan = self._plan(order, approve=True)
        original = order.oct_dispatch_promise_ids.current_date
        first = self._send(order, 100)
        self.assertEqual(first.move_ids.oct_shipment_plan_id, plan.sudo())
        self.assertEqual(order.order_line.qty_delivered, 100)
        self.assertTrue(plan._valid())
        self.assertEqual(sum(self._pickings(order).move_ids.mapped("product_uom_qty")), 500)
        self._send(order, 500)
        self.assertEqual(order.order_line.qty_delivered, 600)
        self.assertFalse(plan._open_batches())
        self.assertEqual(order.oct_dispatch_promise_ids.current_date, original)

    def test_batch_date_priority_does_not_promote_entire_balance(self):
        corporation = self._order(600, "corporate", "2030-12-16")
        consumer = self._order(200, "consumer", "2030-12-15")
        self._seed(300)
        self._plan(corporation, approve=True)
        self._reconcile()
        self.assertEqual([self._reserved(corporation), self._reserved(consumer)], [100, 200])

    def test_changed_batch_quantity_or_combined_batches_need_new_approval(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self._plan(order, approve=True)
        for quantity in (50, 101, 500, 600):
            self._reject(lambda: self._send(order, quantity), order)

    def test_latest_date_inclusive_then_overdue_requires_accepted_replacement(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self._plan(order, approve=True)
        with patch("odoo.fields.Date.context_today", return_value=date(2030, 12, 15)):
            self._reject(lambda: self._send(order, 100), order)
            replacement = self._plan(order, (100, 500), ("2030-12-16", "2030-12-20"))
            self._reject(lambda: self._send(order, 100), order)
            self._answer(replacement)
        with patch("odoo.fields.Date.context_today", return_value=date(2030, 12, 16)):
            self._send(order, 100)

    def test_rejected_replacement_keeps_old_accepted_plan(self):
        order = self._order(600, "corporate")
        self._seed(600)
        original = self._plan(order, approve=True)
        replacement = self._plan(order, (200, 400))
        self._answer(replacement, "rejected")
        self.assertEqual(order._shipment_current_plan(), original)
        self._reject(lambda: self._send(order, 200), order)
        self._send(order, 100)

    def test_reapprove_remaining_after_dispatch_keeps_completed_batch(self):
        order = self._order(600, "corporate")
        self._seed(600)
        original = self._plan(order, approve=True)
        first = self._send(order, 100)
        replacement = self._plan(order, (200, 300), ("2030-12-19", "2030-12-20"), approve=True)
        self._send(order, 200)
        self._send(order, 300)
        self.assertEqual(first.move_ids.oct_shipment_plan_id, original.sudo())
        self.assertEqual(order._shipment_current_plan(), replacement)
        self.assertEqual(order.order_line.qty_delivered, 600)

    def test_order_quantity_change_and_restore_invalidate_approval(self):
        order = self._order(600, "corporate")
        self._seed(600)
        plan = self._plan(order, approve=True)
        order.order_line.write({"product_uom_qty": 601})
        order.order_line.write({"product_uom_qty": 600})
        self.assertFalse(plan._valid())
        self._reject(lambda: self._send(order, 100), order)
        self._plan(order, approve=True)
        self._send(order, 100)

    def test_stale_pending_response_cannot_become_approval(self):
        order = self._order(600, "corporate")
        plan = self._plan(order)
        order.order_line.write({"product_uom_qty": 601})
        self.assertFalse(self._answer(plan))
        self.assertEqual(plan.state, "stale")
        self.assertEqual(plan.response_decision, "accepted")
        self.assertFalse(order._shipment_current_plan())

    def test_proposal_must_cover_all_quantities_and_valid_batch_dates(self):
        order = self._order(600, "corporate")
        for quantities in ((100,), (100, 501), (-100, 700), (float("nan"), 500)):
            with self.assertRaises(UserError), self.cr.savepoint():
                self._plan(order, quantities, ("2030-12-14", "2030-12-18"))
        with self.assertRaises(UserError), self.cr.savepoint():
            self._plan(order, dates=("2030-12-18", "2030-12-14"))

    def test_history_cannot_be_forged_by_crud_sudo_context_or_copy(self):
        order = self._order(600, "corporate")
        plan = self._plan(order, approve=True)
        for record in (plan, plan.row_ids):
            with self.assertRaises(AccessError):
                record.sudo().write({"quantity": 1} if record._name.endswith("row") else {"state": "accepted"})
            with self.assertRaises(AccessError):
                record.sudo().unlink()
        with self.assertRaises(AccessError):
            plan.copy()
        with self.assertRaises(AccessError):
            self.env["oct.shipment.plan"].sudo().create({"order_id": order.id, "state": "accepted"})
        with self.assertRaises(AccessError):
            order.write({"oct_shipment_scope_revision": 0})
        move = self._pickings(order).move_ids
        with self.assertRaises(AccessError):
            move.sudo().with_context(_oct_plan_token=True).write({"oct_shipment_plan_id": plan.id})

    def test_only_authorized_coordinator_can_record_customer_evidence(self):
        order = self._order(600, "corporate")
        plan = self._plan(order)
        for role in (self.stock_user, self.plain_user, self.portal):
            with self.assertRaises(AccessError):
                self._answer(self._as(plan, role))
        with self.assertRaises(UserError):
            plan.respond("accepted", "", "email", fields.Datetime.now(), "")
        self.assertTrue(self._answer(plan))

    def test_response_replay_is_idempotent_and_different_response_is_blocked(self):
        order = self._order(600, "corporate")
        plan = self._plan(order, approve=True)
        self.assertTrue(plan.respond("accepted", plan.response_person, plan.response_channel, plan.response_at, plan.response_evidence))
        with self.assertRaises(UserError):
            self._answer(plan, "rejected")

    def test_date_only_acceptance_cannot_rewrite_quantity_plan(self):
        order = self._order(600, "corporate")
        self._plan(order, approve=True)
        proposal = self._proposal(order, "2030-12-20")
        with self.assertRaises(UserError):
            self._respond(proposal, "accepted")
        self.assertEqual(order.oct_dispatch_promise_ids.current_date, date(2030, 12, 15))

    def test_raw_move_completion_cannot_skip_batch_approval(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self._reconcile()
        def bypass():
            picking = self._pickings(order)
            self._prepare(picking, 100)
            picking.move_ids.with_context(skip_backorder=True, _oct_plan_token=True)._action_done()
        self._reject(bypass, order)

    def test_multiline_batch_requires_exact_quantities_for_each_line(self):
        order = self._order(policy="corporate", lines=[(self.product, 10, self.unit), (self.second_product, 20, self.unit)])
        self._seed(10)
        self._seed(20, self.second_product)
        rows = []
        for batch, fraction in ((1, .4), (2, .6)):
            for line in order.order_line:
                rows.append({"batch": batch, "line_id": line.id, "quantity": line.product_uom_qty * fraction, "latest_date": "2030-12-18"})
        model = self._as(self.env["oct.shipment.plan"])
        plan = model.browse(model.propose(order.id, rows, "Synthetic multi-line proposal"))
        self._answer(plan)
        picking = self._pickings(order)
        for move in picking.move_ids:
            move.write({"quantity": move.product_uom_qty * .4, "picked": True})
        self.assertNotIsInstance(picking.button_validate(), dict)
        self.assertTrue(plan._valid())
        self.assertEqual(sorted(order.order_line.mapped("qty_delivered")), [4, 8])

    def test_proposal_and_response_forms_resolve_and_record_evidence(self):
        order = self._order(600, "corporate")
        action = order.action_propose_shipment_plan()
        model = self._as(self.env["oct.shipment.plan.wizard"]).with_context(**action["context"])
        with Form(model) as wizard:
            wizard.reason = "Synthetic form proposal"
            for number, qty in ((1, 100), (2, 500)):
                with wizard.row_ids.new() as row:
                    row.batch = number
                    row.sale_line_id = order.order_line
                    row.quantity = qty
                    row.latest_date = "2030-12-18"
        result = wizard.record.action_apply()
        plan = self._as(self.env["oct.shipment.plan"]).browse(result["res_id"])
        action = plan.action_respond()
        response_model = self._as(self.env["oct.shipment.plan.wizard"]).with_context(**action["context"])
        with Form(response_model) as response:
            response.decision = "accepted"
            response.person = "Synthetic Contact"
            response.channel = "email"
            response.evidence = "Synthetic form evidence"
        response.record.action_apply()
        self.assertEqual(plan.state, "accepted")

    def test_plan_quantities_use_sales_uom_and_real_backorder_conversion(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        order = self._order(policy="corporate", lines=[(self.product, 2, dozen)])
        self._seed(12)
        plan = self._plan(order, (1, 1), approve=True)
        move = self._pickings(order).move_ids
        self._send(order, dozen._compute_quantity(1, move.product_uom))
        self.assertTrue(plan._valid())
        self.assertEqual(order.order_line.qty_delivered, 1)
        self._seed(12)
        self._reconcile()
        move = self._pickings(order).move_ids.filtered(lambda item: item.state not in ("done", "cancel"))
        self._send(order, dozen._compute_quantity(1, move.product_uom))
        self.assertEqual(order.order_line.qty_delivered, 2)
        self.assertEqual(self.product.qty_available, 0)

    def test_prepared_stock_must_be_reviewed_before_accepting_replacement(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self._reconcile()
        self._prepare(self._pickings(order), 100)
        plan = self._plan(order)
        with self.assertRaisesRegex(UserError, "unprepare"):
            self._answer(plan)
        self.assertEqual(plan.state, "pending")
        self.assertEqual(self._reserved(order), 100)

    def test_foreign_company_and_invisible_sales_order_cannot_read_or_approve(self):
        order = self._order(600, "corporate")
        plan = self._plan(order)
        foreign_company = self.env["res.company"].create({"name": "Synthetic Plan Foreign Company"})
        foreign = self._user("plan_foreign", ["sales_team.group_sale_salesman_all_leads",
            "operations_dispatch_promise.group_dispatch_coordinator"], company=foreign_company)
        restricted = self._user("plan_restricted", ["sales_team.group_sale_salesman",
            "operations_dispatch_promise.group_dispatch_coordinator"])
        for actor in (foreign, restricted):
            scoped = self._as(self.env["oct.shipment.plan"], actor)
            self.assertFalse(scoped.search([("id", "=", plan.id)]))
            with self.assertRaises(AccessError):
                self._answer(scoped.browse(plan.id))

    def test_foreign_line_duplicate_row_and_invalid_numbers_cannot_form_plan(self):
        order = self._order(600, "corporate")
        outside = self._order(600, "corporate")
        model = self._as(self.env["oct.shipment.plan"])
        valid = {"batch": 1, "line_id": order.order_line.id, "quantity": 600, "latest_date": "2030-12-18"}
        for rows in ([valid, valid], [{**valid, "line_id": outside.order_line.id}],
                     [{**valid, "quantity": float("inf")}], [{**valid, "batch": 0}],
                     [{**valid, "batch": True}]):
            with self.assertRaises(UserError), self.cr.savepoint():
                model.propose(order.id, rows, "Synthetic invalid proposal")

    def test_expired_pending_acceptance_is_evidence_not_permission_and_can_be_replaced(self):
        order = self._order(600, "corporate")
        plan = self._plan(order)
        with patch("odoo.fields.Date.context_today", return_value=date(2030, 12, 15)):
            self.assertFalse(self._answer(plan))
            self.assertEqual(plan.state, "stale")
            self.assertEqual(plan.response_decision, "accepted")
            self._plan(order, dates=("2030-12-16", "2030-12-20"), approve=True)
        self.assertNotEqual(order._shipment_current_plan(), plan)

    def test_expired_unanswered_plan_can_be_superseded_without_fake_rejection(self):
        order = self._order(600, "corporate")
        plan = self._plan(order)
        with patch("odoo.fields.Date.context_today", return_value=date(2030, 12, 15)):
            self._plan(order, dates=("2030-12-16", "2030-12-20"), approve=True)
            self.assertEqual(plan.state, "stale")
            self.assertFalse(self._answer(plan))
        self.assertEqual(plan.state, "stale")
        self.assertEqual(plan.response_decision, "accepted")

    def test_return_cannot_resurrect_an_already_superseded_pending_plan(self):
        order = self._order(2, "corporate")
        self._seed(2)
        self._plan(order, (1, 1), approve=True)
        pending = self._plan(order, (2,))
        first = self._send(order, 1)
        self._plan(order, (1,))
        self.assertEqual(pending.state, "stale")
        customer_location = self.env.ref("stock.stock_location_customers")
        returned = self._as(self.env["stock.picking"], self.stock_user).create({
            "picking_type_id": self.warehouse.in_type_id.id,
            "location_id": customer_location.id, "location_dest_id": self.warehouse.lot_stock_id.id,
            "move_ids": [Command.create({"product_id": self.product.id, "product_uom_qty": 1,
                "product_uom": self.unit.id, "location_id": customer_location.id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "origin_returned_move_id": first.move_ids.id, "sale_line_id": order.order_line.id})],
        })
        returned.action_confirm()
        returned.move_ids.write({"quantity": 1, "picked": True})
        returned.button_validate()
        self.assertEqual(order.order_line.qty_delivered, 0)
        self.assertFalse(pending._valid())
        self.assertFalse(self._answer(pending))
        self.assertEqual(pending.state, "stale")
        self.assertNotEqual(order._shipment_current_plan(), pending)

    def test_context_defaults_cannot_fabricate_approval_or_batch_quantities(self):
        order = self._order(600, "corporate")
        model = self._as(self.env["oct.shipment.plan"]).with_context(
            default_state="accepted", default_response_person="Forged", default_response_at="2030-01-01",
            default_quantity=999, default_batch=999, default_latest_date="2099-01-01",
        )
        plan = model.browse(model.propose(order.id, [
            {"batch": 1, "line_id": order.order_line.id, "quantity": 600, "latest_date": "2030-12-18"}
        ], "Synthetic default-context probe"))
        self.assertEqual(plan.state, "pending")
        self.assertFalse(plan.response_person)
        self.assertFalse(plan.response_at)
        self.assertEqual(plan.row_ids.batch, 1)
        self.assertEqual(plan.row_ids.quantity, 600)
        self.assertEqual(plan.row_ids.latest_date, date(2030, 12, 18))

    def test_rpc_timezone_cannot_extend_warehouse_latest_dispatch_date(self):
        order = self._order(600, "corporate")
        self._seed(600)
        self.warehouse.partner_id.tz = "UTC"
        self._plan(order, approve=True)
        def local_day(record):
            return date(2030, 12, 15) if record.env.context.get("tz") == "UTC" else date(2030, 12, 14)
        with patch("odoo.fields.Date.context_today", side_effect=local_day):
            self._reject(lambda: self._send(order.with_context(tz="Pacific/Honolulu"), 100), order)
