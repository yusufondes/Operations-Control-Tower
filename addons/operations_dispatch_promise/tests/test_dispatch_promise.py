"""Synthetic normal-role acceptance tests for TASK-0004, not customer consent."""

from copy import deepcopy
from datetime import date, datetime
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDispatchPromise(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create({
            "name": "Synthetic Dispatch Secondary Company",
        })
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.warehouse = cls.env["stock.warehouse"].search([
            ("company_id", "=", cls.company.id),
        ], limit=1)
        cls.warehouse.out_type_id.write({
            "reservation_method": "manual", "create_backorder": "always",
        })
        cls.product = cls.env["product.product"].create({
            "name": "Synthetic Dispatch Goods", "type": "consu",
            "is_storable": True, "tracking": "none", "uom_id": cls.unit.id,
        })
        cls.customer = cls.env["res.partner"].create({
            "name": "Synthetic Dispatch Corporate", "is_company": True,
        })
        cls.coordinator = cls._user("coordinator", [
            "sales_team.group_sale_salesman",
            "operations_dispatch_promise.group_dispatch_coordinator",
        ])
        cls.salesperson = cls._user("salesperson", [
            "sales_team.group_sale_salesman",
        ])
        cls.coordinator_only = cls._user("coordinator_only", [
            "operations_dispatch_promise.group_dispatch_coordinator",
        ])
        cls.portal = cls._user("portal", ["base.group_portal"])
        cls.foreign_coordinator = cls._user("foreign_coordinator", [
            "sales_team.group_sale_salesman",
            "operations_dispatch_promise.group_dispatch_coordinator",
        ], company=cls.other_company)

    @classmethod
    def _user(cls, suffix, groups, company=None):
        company = company or cls.company
        return cls.env["res.users"].create({
            "name": f"Synthetic Dispatch {suffix}",
            "login": f"synthetic_dispatch_{suffix}",
            "company_id": company.id,
            "company_ids": [Command.set(company.ids)],
            "group_ids": [Command.set([cls.env.ref(g).id for g in groups])],
        })

    def _as(self, records, user=None):
        user = user or self.coordinator
        return records.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids,
        )

    def _order(self, quantity=10, user=None, company=None, confirm=True):
        company = company or self.company
        user = user or self.coordinator
        warehouse = self.env["stock.warehouse"].search([
            ("company_id", "=", company.id),
        ], limit=1)
        if not warehouse:
            warehouse = self.env["stock.warehouse"].create({
                "name": "Synthetic Secondary Warehouse", "code": "SDP2",
                "company_id": company.id,
            })
        order = self.env["sale.order"].with_company(company).create({
            "partner_id": self.customer.id, "company_id": company.id,
            "user_id": user.id, "warehouse_id": warehouse.id,
            "picking_policy": "direct",
            "commitment_date": "2030-12-14 12:00:00",
            "order_line": [Command.create({
                "product_id": self.product.id, "name": self.product.name,
                "product_uom_qty": quantity, "product_uom_id": self.unit.id,
                "price_unit": 10, "tax_ids": [Command.clear()],
            })],
        })
        if confirm:
            order.action_confirm()
        return order

    def _promise(self, order=None, initial="2030-12-15", user=None):
        order = order if order is not None else self._order()
        model = self._as(self.env["oct.dispatch.promise"], user)
        return model.browse(model.establish(order.id, initial))

    def _proposal(self, promise, proposed="2030-12-20"):
        return self._as(self.env["oct.dispatch.proposal"]).browse(
            promise.propose(proposed, "Synthetic supplier delay"),
        )

    def _respond(self, proposal, decision="accepted", **changes):
        values = {
            "decision": decision, "person": "Synthetic Customer Contact",
            "channel": "email", "at": "2030-12-01 10:00:00",
            "evidence": "Synthetic manual email reference TEST-001",
        }
        values.update(changes)
        return proposal.respond(
            values["decision"], values["person"], values["channel"],
            values["at"], values["evidence"],
        )

    def _dispatch(self, order, quantity):
        # Real standard stock dispatch, not a write to sale qty_delivered.
        warehouse = order.warehouse_id
        self.env["stock.quant"]._update_available_quantity(
            self.product, warehouse.lot_stock_id, quantity,
        )
        picking = order.picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel"),
        )
        picking.ensure_one()
        picking.action_assign()
        move = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
        move.ensure_one()
        move.write({"quantity": quantity, "picked": True})
        result = picking.button_validate()
        self.assertNotIsInstance(result, dict, "Unexpected dispatch wizard")
        self.assertEqual(picking.state, "done")
        return picking

    def _schedule(self, order):
        return (
            order.commitment_date,
            [(m.id, m.date_deadline, m.date) for m in order.picking_ids.move_ids],
            [(p.id, p.scheduled_date) for p in order.picking_ids],
        )

    def test_a01_initial_and_proposal_do_not_reschedule_stock(self):
        order = self._order()
        schedule = self._schedule(order)
        promise = self._promise(order)
        proposal = self._proposal(promise)
        self.assertEqual(promise.original_date, date(2030, 12, 15))
        self.assertEqual(promise.current_date, promise.original_date)
        self.assertEqual(proposal.proposed_date, date(2030, 12, 20))
        self.assertEqual(proposal.state, "pending")
        self.assertEqual(proposal.base_revision, promise.revision)
        self.assertEqual(self._schedule(order), schedule)

    def test_a02_unanswered_and_estimate_are_not_acceptance_or_messages(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        mail_count = self.env["mail.mail"].search_count([])
        message_count = self.env["mail.message"].search_count([
            ("model", "=", "sale.order"), ("res_id", "=", order.id),
        ])
        promise.set_estimate("2030-12-19")
        self.assertEqual(promise.estimate_date, date(2030, 12, 19))
        self.assertEqual(promise.current_date, date(2030, 12, 15))
        self.assertEqual(proposal.state, "pending")
        self.assertFalse(proposal.response_decision)
        self.assertEqual(self.env["mail.mail"].search_count([]), mail_count)
        self.assertEqual(self.env["mail.message"].search_count([
            ("model", "=", "sale.order"), ("res_id", "=", order.id),
        ]), message_count)
        promise.set_estimate(False)
        self.assertFalse(promise.estimate_date)

    def test_a03_explicit_acceptance_preserves_audit_and_standard_dates(self):
        order = self._order()
        schedule = self._schedule(order)
        promise = self._promise(order)
        self.assertFalse(promise.env.su, "Acceptance must exercise a normal role")
        proposal = self._proposal(promise)
        snapshot = deepcopy(proposal.scope_snapshot)
        revision = promise.revision
        self.assertTrue(self._respond(proposal))
        self.assertEqual(promise.current_date, date(2030, 12, 20))
        self.assertEqual(promise.original_date, date(2030, 12, 15))
        self.assertEqual(promise.revision, revision + 1)
        self.assertEqual(proposal.base_revision, revision)
        self.assertEqual(proposal.state, "accepted")
        self.assertTrue(proposal.applied)
        self.assertEqual(proposal.response_user_id, self.coordinator)
        self.assertEqual(proposal.response_person, "Synthetic Customer Contact")
        self.assertEqual(proposal.response_channel, "email")
        self.assertEqual(proposal.response_at, datetime(2030, 12, 1, 10))
        self.assertIn("TEST-001", proposal.response_evidence)
        self.assertEqual(proposal.scope_snapshot, snapshot)
        self.assertEqual(self._schedule(order), schedule)

    def test_a04_rejection_preserves_late_initial_promise(self):
        promise = self._promise(initial="2000-01-01")
        proposal = self._proposal(promise)
        revision = promise.revision
        self.assertTrue(self._respond(proposal, "rejected"))
        self.assertEqual(proposal.state, "rejected")
        self.assertEqual(proposal.response_decision, "rejected")
        self.assertFalse(proposal.applied)
        self.assertEqual(promise.revision, revision)
        self.assertEqual(promise.current_date, date(2000, 1, 1))
        self.assertEqual(promise.original_date, promise.current_date)

    def test_a05_corporate_completed300_snapshot_remaining300(self):
        order = self._order(quantity=600)
        completed = self._dispatch(order, 300)
        self.assertEqual(order.order_line.qty_delivered, 300)
        completed_values = completed.read(["state", "date_done"])
        completed_moves = completed.move_ids.read(["quantity", "state"])
        promise = self._promise(order)
        proposal = self._proposal(promise)
        lines = proposal.scope_snapshot["lines"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["remaining"], 300)
        self.assertEqual(lines[0]["delivered"], 300)
        self.assertEqual(lines[0]["ordered"], 600)
        self.assertTrue(self._respond(proposal))
        self.assertEqual(completed.read(["state", "date_done"]), completed_values)
        self.assertEqual(completed.move_ids.read(["quantity", "state"]), completed_moves)
        self.assertEqual(order.order_line.qty_delivered, 300)

    def test_a06_partial_dispatch_stales_and_retains_customer_response(self):
        order = self._order(quantity=600)
        promise = self._promise(order)
        proposal = self._proposal(promise)
        self._dispatch(order, 300)
        self.assertTrue(proposal.is_stale)
        self.assertFalse(self._respond(proposal))
        self.assertEqual(proposal.state, "stale")
        self.assertEqual(proposal.response_decision, "accepted")
        self.assertTrue(proposal.response_evidence)
        self.assertFalse(proposal.applied)
        self.assertEqual(promise.current_date, promise.original_date)
        fresh = self._proposal(promise, "2030-12-22")
        self.assertEqual(fresh.scope_snapshot["lines"][0]["remaining"], 300)

    def test_a06_changed_and_restored_quantity_cannot_revive_proposal(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        order.order_line.product_uom_qty = 11
        self.assertTrue(proposal.is_stale)
        order.order_line.product_uom_qty = 10
        self.assertTrue(proposal.is_stale)
        self.assertFalse(self._respond(proposal))
        self.assertEqual(proposal.state, "stale")
        self.assertEqual(promise.current_date, promise.original_date)

    def test_a06_cancellation_and_reconfirmation_do_not_revive_proposal(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        order.with_context(disable_cancel_warning=True).action_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertTrue(proposal.is_stale)
        order.action_draft()
        order.action_confirm()
        self.assertTrue(proposal.is_stale)
        self.assertFalse(self._respond(proposal))
        self.assertEqual(proposal.state, "stale")
        self.assertEqual(promise.current_date, promise.original_date)

    def test_a07_identical_retries_and_conflicts_are_safe(self):
        promise = self._promise()
        proposal = self._proposal(promise)
        with self.assertRaises(UserError):
            self._proposal(promise, "2030-12-22")
        self.assertTrue(self._respond(proposal))
        revision = promise.revision
        response_values = proposal.read([
            "state", "response_decision", "response_at", "response_user_id",
        ])
        self.assertTrue(self._respond(proposal))
        self.assertEqual(promise.revision, revision)
        self.assertEqual(proposal.read([
            "state", "response_decision", "response_at", "response_user_id",
        ]), response_values)
        with self.assertRaises(UserError):
            self._respond(proposal, "rejected")
        with self.assertRaises(UserError):
            self._respond(proposal, evidence="Conflicting synthetic evidence")
        self.assertEqual(promise.revision, revision)
        self.assertEqual(len(promise.proposal_ids), 1)

    def test_a07_stale_response_never_overwrites_newer_acceptance(self):
        order = self._order()
        promise = self._promise(order)
        stale = self._proposal(promise)
        order.order_line.product_uom_qty = 11
        fresh = self._proposal(promise, "2030-12-22")
        self.assertEqual(stale.state, "stale")
        self.assertTrue(self._respond(fresh))
        revision = promise.revision
        self.assertFalse(self._respond(stale))
        self.assertFalse(self._respond(stale))
        self.assertEqual(promise.current_date, date(2030, 12, 22))
        self.assertEqual(promise.revision, revision)
        self.assertEqual(stale.response_decision, "accepted")
        self.assertFalse(stale.applied)

    def test_a09_missing_initial_cancelled_or_fulfilled_demand_is_rejected(self):
        order = self._order()
        model = self._as(self.env["oct.dispatch.promise"])
        for initial in (False, "not-a-date"):
            with self.assertRaises(UserError):
                model.establish(order.id, initial)
        self.assertFalse(model.search([("order_id", "=", order.id)]))
        draft = self._order(confirm=False)
        with self.assertRaises(UserError):
            self._promise(draft)
        cancelled = self._order()
        cancelled.with_context(disable_cancel_warning=True).action_cancel()
        with self.assertRaises(UserError):
            self._promise(cancelled)
        self._dispatch(order, 10)
        with self.assertRaises(UserError):
            self._promise(order)

    def test_a09_bad_response_evidence_is_atomic(self):
        promise = self._promise()
        proposal = self._proposal(promise)
        for changes in (
            {"person": ""}, {"person": "   "}, {"channel": ""},
            {"channel": "carrier"}, {"at": False}, {"at": "not-a-date"},
            {"evidence": ""}, {"evidence": "   "}, {"decision": "pending"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(UserError):
                    with self.cr.savepoint():
                        self._respond(proposal, **changes)
                self.assertEqual(proposal.state, "pending")
                self.assertFalse(proposal.response_decision)
                self.assertEqual(promise.current_date, promise.original_date)
                self.assertEqual(promise.revision, 1)

    def test_a12_rejected_or_unanswered_second_proposal_keeps_latest_promise(self):
        promise = self._promise()
        accepted = self._proposal(promise)
        self.assertTrue(self._respond(accepted))
        rejected = self._proposal(promise, "2030-12-23")
        self.assertTrue(self._respond(rejected, "rejected"))
        pending = self._proposal(promise, "2030-12-24")
        promise.set_estimate("2030-12-26")
        self.assertEqual(promise.current_date, date(2030, 12, 20))
        self.assertEqual(promise.original_date, date(2030, 12, 15))
        self.assertEqual(pending.state, "pending")
        self.assertEqual(set(promise.proposal_ids.ids), {
            accepted.id, rejected.id, pending.id,
        })

    def test_a08_role_and_company_do_not_grant_source_order_access(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        for user in (
            self.salesperson, self.coordinator_only, self.portal,
            self.foreign_coordinator,
        ):
            with self.subTest(user=user.login):
                actions = [
                    lambda: self._as(self.env["oct.dispatch.promise"], user).establish(
                        order.id, "2030-12-15",
                    ),
                    lambda: self._as(promise, user).propose(
                        "2030-12-22", "Unauthorized proposal",
                    ),
                    lambda: self._as(promise, user).set_estimate("2030-12-23"),
                    lambda: self._respond(self._as(proposal, user)),
                ]
                for action in actions:
                    with self.assertRaises(AccessError):
                        with self.cr.savepoint():
                            action()
                self.assertEqual(promise.current_date, promise.original_date)
                self.assertFalse(proposal.response_decision)
        self.assertFalse(self.coordinator_only.has_group(
            "sales_team.group_sale_salesman",
        ))
        foreign_order = self._order(
            user=self.foreign_coordinator, company=self.other_company,
        )
        foreign_promise = self._promise(
            foreign_order, user=self.foreign_coordinator,
        )
        self.assertEqual(foreign_promise.company_id, self.other_company)
        self.assertFalse(self._as(self.env["oct.dispatch.promise"]).search([
            ("id", "=", foreign_promise.id),
        ]))
        with self.assertRaises(AccessError):
            self._as(foreign_promise).read(["current_date"])

    def test_a08_source_assignment_changes_hide_promise_and_history(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        self.assertTrue(promise.read(["current_date"]))
        self.assertTrue(proposal.read(["reason"]))
        order.user_id = self.salesperson
        for record in (promise, proposal):
            with self.subTest(model=record._name):
                model = self._as(self.env[record._name])
                self.assertFalse(model.search([("id", "=", record.id)]))
                self.assertEqual(model.search_count([("id", "=", record.id)]), 0)
                with self.assertRaises(AccessError):
                    record.read(["id"])
                with self.assertRaises(AccessError):
                    record.read(["display_name"])
        with self.assertRaises(AccessError):
            self._respond(proposal)
        order.user_id = self.coordinator
        self.assertTrue(promise.read(["current_date"]))
        self.assertEqual(promise.current_date, date(2030, 12, 15))
        self.assertTrue(proposal.read(["reason"]))

    def test_a08_actions_need_source_write_not_just_source_read(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        self.env["ir.rule"].create({
            "name": "Synthetic source order write restriction",
            "model_id": self.env.ref("sale.model_sale_order").id,
            "domain_force": repr([("id", "!=", order.id)]),
            "perm_read": False, "perm_write": True,
            "perm_create": False, "perm_unlink": False,
        })
        self.assertTrue(self._as(order).read(["name"]))
        self.assertTrue(promise.read(["current_date"]))
        with self.assertRaises(AccessError):
            self._as(order).check_access("write")
        for action in (
            lambda: promise.set_estimate("2030-12-22"),
            lambda: promise.propose("2030-12-22", "No source write access"),
            lambda: self._respond(proposal),
        ):
            with self.assertRaises(AccessError):
                with self.cr.savepoint():
                    action()
        self.assertFalse(proposal.response_decision)
        self.assertEqual(promise.revision, 1)

    def test_a08_direct_crud_and_context_flags_cannot_bypass_history(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        context_flags = {
            "dispatch_promise_internal": True, "oct_dispatch_internal": True,
            "skip_dispatch_security": True, "skip_access_check": True,
        }
        promise = promise.with_context(**context_flags)
        proposal = proposal.with_context(**context_flags)
        actions = [
            lambda: promise.create({
                "order_id": order.id, "original_date": "2030-12-01",
                "current_date": "2030-12-01", "responsible_id": self.coordinator.id,
            }),
            lambda: proposal.create({
                "promise_id": promise.id, "proposed_date": "2030-12-25",
                "reason": "Direct create bypass",
            }),
            lambda: promise.write({"current_date": "2030-12-25"}),
            lambda: promise.write({"original_date": "2030-12-25"}),
            lambda: promise.write({"revision": 99}),
            lambda: self._as(order).with_context(**context_flags).write({
                "oct_dispatch_guard_revision": 99,
            }),
            lambda: proposal.write({"state": "accepted", "applied": True}),
            lambda: proposal.write({"scope_snapshot": {}}),
            lambda: promise.unlink(), lambda: proposal.unlink(),
        ]
        for action in actions:
            with self.assertRaises(AccessError):
                with self.cr.savepoint():
                    action()
        self.assertTrue(self._respond(proposal))
        for action in (
            lambda: proposal.write({"response_evidence": "Rewritten history"}),
            lambda: proposal.write({"response_at": "2031-01-01 00:00:00"}),
            lambda: proposal.unlink(),
        ):
            with self.assertRaises(AccessError):
                with self.cr.savepoint():
                    action()
        self.assertEqual(promise.current_date, date(2030, 12, 20))
        self.assertEqual(proposal.response_evidence,
                         "Synthetic manual email reference TEST-001")

    def test_a08_context_defaults_cannot_fabricate_response_history(self):
        order = self._order()
        model = self._as(self.env["oct.dispatch.promise"]).with_context(
            default_revision=99, default_state="accepted",
            default_response_decision="accepted", default_response_person="Fake",
            default_applied=True,
        )
        promise = model.browse(model.establish(order.id, "2030-12-15"))
        proposal = model.env["oct.dispatch.proposal"].browse(
            promise.propose("2030-12-20", "Synthetic customer proposal"),
        )
        self.assertFalse(promise.env.su)
        self.assertEqual(promise.revision, 1)
        self.assertEqual(promise.current_date, date(2030, 12, 15))
        self.assertEqual(promise.original_date, promise.current_date)
        self.assertEqual(proposal.base_revision, 1)
        self.assertEqual(proposal.state, "pending")
        self.assertFalse(proposal.response_decision)
        self.assertFalse(proposal.response_person)
        self.assertFalse(proposal.response_at)
        self.assertFalse(proposal.response_user_id)
        self.assertFalse(proposal.applied)

    def test_a06_warehouse_only_user_can_dispatch_and_stale_proposal(self):
        warehouse_user = self._user("warehouse_only", [
            "base.group_user", "stock.group_stock_user",
        ])
        self.assertFalse(warehouse_user.has_group("sales_team.group_sale_salesman"))
        self.assertFalse(warehouse_user.has_group(
            "operations_dispatch_promise.group_dispatch_coordinator",
        ))
        order = self._order(quantity=600)
        promise = self._promise(order)
        proposal = self._proposal(promise)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.warehouse.lot_stock_id, 300,
        )
        picking = self._as(order.picking_ids, warehouse_user)
        picking.ensure_one()
        self.assertFalse(picking.env.su)
        picking.action_assign()
        move = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
        move.ensure_one()
        move.write({"quantity": 300, "picked": True})
        result = picking.button_validate()
        self.assertNotIsInstance(result, dict, "Unexpected dispatch wizard")
        self.assertEqual(picking.state, "done")
        self.assertEqual(order.order_line.qty_delivered, 300)
        self.assertTrue(proposal.is_stale)
        self.assertEqual(promise.current_date, promise.original_date)

    def test_a08_filtered_access_handles_mixed_source_and_company_denials(self):
        visible = self._promise()
        hidden_order = self._order()
        hidden = self._promise(hidden_order)
        hidden_order.user_id = self.salesperson
        foreign_order = self._order(
            user=self.foreign_coordinator, company=self.other_company,
        )
        foreign = self._promise(foreign_order, user=self.foreign_coordinator)
        mixed = self._as(self.env["oct.dispatch.promise"].browse([
            visible.id, hidden.id, foreign.id,
        ]))
        self.assertEqual(mixed._filtered_access("read").ids, visible.ids)

    def test_a06_stale_response_wizard_returns_complete_notification_next_action(self):
        order = self._order()
        promise = self._promise(order)
        proposal = self._proposal(promise)
        initial_date, revision = promise.current_date, promise.revision
        order.order_line.product_uom_qty = 11
        self.assertTrue(proposal.is_stale)
        wizard = self._as(self.env["oct.dispatch.wizard"]).create({
            "operation": "respond", "order_id": order.id,
            "promise_id": promise.id, "proposal_id": proposal.id,
            "decision": "accepted", "response_person": "Synthetic Customer Contact",
            "response_channel": "email", "response_at": "2030-12-01 10:00:00",
            "response_evidence": "Synthetic stale UI response TEST-UI-001",
        })
        self.assertFalse(wizard.env.su)
        action = wizard.action_apply()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "warning")
        next_action = action["params"]["next"]
        self.assertEqual(next_action["type"], "ir.actions.act_window")
        self.assertEqual(next_action["res_model"], "oct.dispatch.promise")
        self.assertEqual(next_action["res_id"], promise.id)
        self.assertEqual(next_action["view_mode"], "form")
        self.assertEqual(next_action["views"], [(False, "form")])
        self.assertEqual(proposal.state, "stale")
        self.assertEqual(proposal.response_decision, "accepted")
        self.assertEqual(proposal.response_evidence,
                         "Synthetic stale UI response TEST-UI-001")
        self.assertEqual(proposal.response_user_id, self.coordinator)
        self.assertFalse(proposal.applied)
        self.assertEqual(promise.current_date, initial_date)
        self.assertEqual(promise.original_date, initial_date)
        self.assertEqual(promise.revision, revision)

    def test_a10_response_failure_rolls_back_promise_and_history_together(self):
        promise = self._promise()
        proposal = self._proposal(promise)
        revision = promise.revision

        def fail_record_response(records, values):
            self.assertEqual(records.promise_id.current_date, date(2030, 12, 20))
            raise RuntimeError("Synthetic response audit failure")

        with patch.object(type(proposal), "_record_response", fail_record_response):
            with self.assertRaisesRegex(RuntimeError, "Synthetic response audit failure"):
                self._respond(proposal)
        self.assertEqual(promise.current_date, promise.original_date)
        self.assertEqual(promise.revision, revision)
        self.assertEqual(proposal.state, "pending")
        self.assertFalse(proposal.response_decision)
        self.assertFalse(proposal.response_evidence)
        self.assertFalse(proposal.applied)
        self.assertTrue(self._respond(proposal))
