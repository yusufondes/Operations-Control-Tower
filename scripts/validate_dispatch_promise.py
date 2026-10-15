"""Post-install real-connection and server-form checks in an owned scenario DB.

Unlike TransactionCase this deliberately commits synthetic fixtures, only after
the strict DB guard. The owning runner must drop this whole disposable DB.
No browser rendering, customer messages or working-database writes occur.
"""

import json
import re

from odoo import Command, api, fields, sql_db
from odoo.exceptions import UserError
from odoo.tests import Form


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname):
    raise RuntimeError("Refusing promise probe writes outside a guarded scenario DB.")
if env["ir.module.module"].search_count([("name", "=", "operations_dispatch_promise"), ("state", "=", "installed")]) != 1:
    raise RuntimeError("The dispatch promise addon is not installed in this test DB.")

company_id = env.company.id
groups = [env.ref(name).id for name in (
    "operations_dispatch_promise.group_dispatch_coordinator", "sales_team.group_sale_salesman_all_leads",
)]
user = env["res.users"].create({
    "name": "Synthetic Promise Race Coordinator", "login": "oct_synthetic_race_coordinator",
    "company_id": company_id, "company_ids": [Command.set([company_id])], "group_ids": [Command.set(groups)],
})
partner = env["res.partner"].create({"name": "Synthetic Promise Race Customer", "is_company": True})
goods = env["product.product"].create({"name": "Synthetic Promise Race SKU", "type": "consu", "is_storable": True})
ctx = {"allowed_company_ids": [company_id]}
connection = sql_db.db_connect(env.cr.dbname)
observations = []


def new_order():
    order = env["sale.order"].create({
        "partner_id": partner.id, "user_id": user.id,
        "order_line": [Command.create({"product_id": goods.id, "product_uom_qty": 10,
                                        "product_uom_id": goods.uom_id.id, "price_unit": 1})],
    })
    order.action_confirm()
    promise_id = env["oct.dispatch.promise"].with_user(user).establish(order.id, "2030-12-15")
    env.cr.commit()  # Synthetic owned DB only; makes fixture visible to real connections.
    return order.id, promise_id


def must_refuse(operation, message):
    try:
        operation()
    except UserError:
        return
    raise AssertionError(message)


def respond(proposal, decision="accepted"):
    return proposal.respond(decision, "Synthetic Customer", "email", "2030-12-01 10:00:00", "Synthetic reference R1")


order_id, promise_id = new_order()
with connection.cursor() as first, connection.cursor() as second:
    first.execute("SELECT pg_backend_pid()")
    pid1 = first.fetchone()[0]
    second.execute("SELECT pg_backend_pid()")
    pid2 = second.fetchone()[0]
    if pid1 == pid2:
        raise AssertionError("Concurrency probe is not using two real connections.")
    a, b = api.Environment(first, user.id, ctx), api.Environment(second, user.id, ctx)
    proposal_id = a["oct.dispatch.promise"].browse(promise_id).propose("2030-12-20", "Synthetic delay")
    must_refuse(lambda: b["oct.dispatch.promise"].browse(promise_id).propose("2030-12-21", "Competing proposal"),
                "Concurrent proposal was not refused.")
    second.rollback()
    first.commit()
    must_refuse(lambda: b["oct.dispatch.promise"].browse(promise_id).propose("2030-12-21", "Second pending proposal"),
                "Two pending proposals were allowed.")
    second.rollback()
    a.invalidate_all()
    if not respond(a["oct.dispatch.proposal"].browse(proposal_id)):
        raise AssertionError("First response was not applied.")
    must_refuse(lambda: respond(b["oct.dispatch.proposal"].browse(proposal_id), "rejected"),
                "Concurrent conflicting response was not refused.")
    second.rollback()
    first.commit()
    b.invalidate_all()
    if not respond(b["oct.dispatch.proposal"].browse(proposal_id)):
        raise AssertionError("Identical accepted response retry was not idempotent.")
    second.commit()
    must_refuse(lambda: respond(b["oct.dispatch.proposal"].browse(proposal_id), "rejected"),
                "Finalized acceptance was overwritten.")
    second.rollback()
    observations.append({"case": "two_real_connection_proposals_and_responses", "backend_pids": [pid1, pid2], "status": "passed"})

env.cr.rollback()
env.invalidate_all()
promise = env["oct.dispatch.promise"].browse(promise_id)
assert promise.current_date == fields.Date.to_date("2030-12-20") and promise.revision == 2
assert len(promise.proposal_ids) == 1

# Phantom insertion AFTER the accepting transaction's earlier RR snapshot.
phantom_order_id, phantom_promise_id = new_order()
phantom_proposal_id = env["oct.dispatch.promise"].with_user(user).browse(phantom_promise_id).propose("2030-12-20", "Phantom probe")
env.cr.commit()
with connection.cursor() as first, connection.cursor() as second:
    a, b = api.Environment(first, user.id, ctx), api.Environment(second, user.id, ctx)
    stale = a["oct.dispatch.proposal"].browse(phantom_proposal_id)
    assert not stale.is_stale  # Establish a real earlier SQL snapshot.
    b["sale.order.line"].create({
        "order_id": phantom_order_id, "product_id": goods.id, "product_uom_qty": 1,
        "product_uom_id": goods.uom_id.id, "price_unit": 1,
    })
    second.commit()
    must_refuse(lambda: respond(stale), "Earlier RR snapshot accepted a phantom scope change.")
    first.rollback()
    a.invalidate_all()
    if respond(a["oct.dispatch.proposal"].browse(phantom_proposal_id)):
        raise AssertionError("Stale proposal changed the promise after refresh.")
    first.commit()
    observations.append({"case": "repeatable_read_new_line_phantom", "status": "passed"})

env.cr.rollback()
env.invalidate_all()
stale = env["oct.dispatch.proposal"].browse(phantom_proposal_id)
assert stale.state == "stale" and stale.response_decision == "accepted" and not stale.applied
assert stale.promise_id.current_date == fields.Date.to_date("2030-12-15")

# Form helper verifies resolved server-side form views/modifiers and wizard flow.
# It is not browser interaction or visual-layout verification.
form_order_id, form_promise_id = new_order()
coordinator = env["oct.dispatch.promise"].with_user(user).browse(form_promise_id)
sale_form = env["sale.order"].with_user(user).get_view(view_type="form")
assert "warehouse_dispatch_promise" in sale_form["arch"]
with Form(env["oct.dispatch.wizard"].with_user(user).with_context(
    default_operation="propose", default_order_id=form_order_id, default_promise_id=form_promise_id,
)) as form:
    form.dispatch_date = fields.Date.to_date("2030-12-22")
    form.reason = "Synthetic form proposal"
wizard = form.save()
wizard.action_apply()
proposal = coordinator.proposal_ids
proposal.ensure_one()
with Form(env["oct.dispatch.wizard"].with_user(user).with_context(
    default_operation="respond", default_order_id=form_order_id,
    default_promise_id=form_promise_id, default_proposal_id=proposal.id,
)) as form:
    form.decision = "accepted"
    form.response_person = "Synthetic Customer"
    form.response_channel = "phone"
    form.response_evidence = "Synthetic call note, no outbound call"
wizard = form.save()
wizard.action_apply()
assert coordinator.current_date == fields.Date.to_date("2030-12-22")
observations.append({"case": "resolved_sales_form_and_wizard_form_helper", "status": "passed", "browser": "not run"})
env.cr.rollback()
print("OCT_PROMISE_RESULT=" + json.dumps({
    "database": env.cr.dbname, "status": "passed", "cases": observations,
    "limitations": ["Browser rendering not tested", "Committed synthetic fixtures removed with owned DB",
                    "No stock scheduling or customer-authentication claim"],
}, sort_keys=True))
