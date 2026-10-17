"""Role-based campaign flow and real-connection probes in an owned scenario DB.

This deliberately commits synthetic fixtures after a strict database guard.
The owning runner must remove the whole DB, including committed race fixtures.
No working database, real customer, supplier interface or carrier is used.
"""

import json
import re
from datetime import date, datetime, timedelta

from odoo import Command, api, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname):
    raise RuntimeError("Refusing campaign fixtures outside an owned scenario database.")
if env["ir.module.module"].search_count([
        ("name", "=", "operations_campaign_automation"), ("state", "=", "installed")]) != 1:
    raise RuntimeError("The campaign addon is not installed in this scenario database.")

results = []
company = env.company
unit = env.ref("uom.product_uom_unit")
warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
warehouse.ensure_one()
warehouse.out_type_id.write({"reservation_method": "manual", "create_backorder": "always"})
context = {"allowed_company_ids": company.ids}
planned = datetime(2030, 12, 15, 12)


def equal(actual, expected, label):
    if float_compare(actual, expected, precision_digits=5):
        raise AssertionError(f"{label}: expected {expected}, observed {actual}")


def passed(case, **evidence):
    results.append({"case": case, "status": "passed", **evidence})


def user(suffix, groups):
    return env["res.users"].create({
        "name": f"Synthetic Campaign Validation {suffix}",
        "login": f"oct_campaign_validation_{suffix}",
        "company_id": company.id, "company_ids": [Command.set(company.ids)],
        "group_ids": [Command.set([env.ref(group).id for group in groups])],
    })


sales = user("sales", ["sales_team.group_sale_salesman_all_leads",
                       "operations_dispatch_promise.group_dispatch_coordinator"])
stock = user("warehouse", ["stock.group_stock_user"])
planner = user("planner", ["stock.group_stock_manager", "purchase.group_purchase_user",
                           "mrp.group_mrp_manager", "operations_dispatch_promise.group_dispatch_coordinator",
                           "operations_control_tower.group_operations_manager"])
if sales.has_group("stock.group_stock_user") or stock.has_group("sales_team.group_sale_salesman"):
    raise AssertionError("Role fixture accidentally combines Sales and warehouse permissions.")


def as_user(records, role):
    return records.with_user(role).with_context(**context)


def goods(name):
    return env["product.product"].create({
        "name": f"Synthetic Campaign Validation {name}", "type": "consu",
        "is_storable": True, "tracking": "none", "uom_id": unit.id, "sale_delay": 0,
    })


main = goods("Drink")
ingredient, packaging = goods("Ingredient"), goods("Packaging")
probe_products = {name: goods(name) for name in ("Acceptance", "Supply Race", "Acceptance Race",
                                               "Order Phantom", "Line Phantom", "Scheduler",
                                               "Move Preparation Race", "Line Preparation Race",
                                               "Plan Acceptance Race", "Plan Dispatch Race")}
pool = as_user(env["oct.campaign.pool"], planner).create({
    "name": "Synthetic Campaign Validation Pool", "warehouse_id": warehouse.id,
    "location_id": warehouse.lot_stock_id.id,
    "product_ids": [Command.set((main | env["product.product"].browse(
        [product.id for product in probe_products.values()])).ids)],
    "responsible_id": planner.id,
})
customer = env["res.partner"].create({"name": "Synthetic Campaign Validation Consumer"})
corporation = env["res.partner"].create({"name": "Synthetic Campaign Validation Corporate", "is_company": True})


def seed(product, quantity):
    # Opening stock fixture only. Subsequent main-SKU supply uses purchase/MRP.
    env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, quantity)


def order(product, quantity, due, policy="corporate", session=None):
    session = session or env
    model = session["sale.order"].with_user(sales.id).with_context(**context)
    record = model.create({
        "partner_id": corporation.id if policy == "corporate" else customer.id,
        "warehouse_id": warehouse.id, "user_id": sales.id,
        "oct_campaign_pool_id": pool.id, "oct_campaign_policy": policy,
        "order_line": [Command.create({
            "product_id": product.id, "name": product.name, "product_uom_qty": quantity,
            "product_uom_id": unit.id, "price_unit": 10, "discount": 20,
            "tax_ids": [Command.clear()],
        })],
    })
    record.action_confirm()
    if due is not None:
        session["oct.dispatch.promise"].with_user(sales.id).with_context(**context).establish(record.id, due)
    return record


def open_pickings(record, session=None):
    session = session or env
    return session["stock.picking"].with_user(stock.id).with_context(**context).search([
        ("sale_id", "=", record.id), ("state", "not in", ["done", "cancel"]),
        ("picking_type_id.code", "=", "outgoing"),
    ])


def reservation(record, session=None):
    session = session or env
    moves = open_pickings(record, session).move_ids.filtered(lambda move: move.state not in ("done", "cancel"))
    return sum(move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id, round=False)
               for move in moves)


def validate(picking, quantity):
    picking.ensure_one()
    moves = picking.move_ids.filtered(lambda move: move.state not in ("done", "cancel"))
    moves.ensure_one()
    moves.write({"quantity": quantity, "picked": True})
    result = picking.button_validate()
    if isinstance(result, dict) or picking.state != "done":
        raise AssertionError("Standard stock completion did not finish without an unexpected wizard.")


def dispatch(record, quantity):
    # Record explicit synthetic customer consent before each changed batch plan.
    if record.oct_campaign_policy == "corporate":
        line = record.order_line
        remaining = line.product_uom_qty - line.qty_delivered
        quantities = [quantity] + ([remaining - quantity] if quantity < remaining else [])
        model = as_user(env["oct.shipment.plan"], sales)
        plan = model.browse(model.propose(record.id, [
            {"batch": i + 1, "line_id": line.id, "quantity": qty,
             "latest_date": record.oct_dispatch_promise_ids.current_date}
            for i, qty in enumerate(quantities)], "Synthetic customer approval for shipment batches"))
        plan.respond("accepted", "Synthetic Customer Contact", "email", fields.Datetime.now(), "Synthetic manual batch consent")
    validate(open_pickings(record), quantity)


def receipt(product, quantity, session):
    picking = session["stock.picking"].with_user(stock.id).with_context(**context).create({
        "picking_type_id": warehouse.in_type_id.id,
        "location_id": warehouse.in_type_id.default_location_src_id.id,
        "location_dest_id": warehouse.lot_stock_id.id,
        "move_ids": [Command.create({
            "product_id": product.id, "product_uom_qty": quantity,
            "product_uom": unit.id, "location_id": warehouse.in_type_id.default_location_src_id.id,
            "location_dest_id": warehouse.lot_stock_id.id,
        })],
    })
    picking.action_confirm()
    validate(picking, quantity)
    return picking


def proposal(record, due, session=None):
    session = session or env
    promise = session["oct.dispatch.promise"].with_user(sales.id).with_context(**context).search([
        ("order_id", "=", record.id),
    ])
    return session["oct.dispatch.proposal"].with_user(sales.id).with_context(**context).browse(
        promise.propose(due, "Synthetic campaign supply delay"))


def respond(record, decision):
    return record.respond(decision, "Synthetic Customer Contact", "email",
                          "2030-12-01 10:00:00", "Synthetic validation response reference")


def must_refuse(operation, label):
    try:
        operation()
    except UserError:
        return
    raise AssertionError(label)


def reconcile(session=None):
    session = session or env
    return session["oct.campaign.pool"].with_user(planner.id).with_context(**context).browse(pool.id).action_reconcile()


# One primary end-to-end scenario: real standard purchase and manufacturing ORM.
seed(main, 500)
last = order(main, 100, "2030-12-17", "consumer")
corporate = order(main, 600, "2030-12-16")
first = order(main, 200, "2030-12-15", "consumer")
initial = [reservation(record) for record in (first, corporate, last)]
for actual, expected in zip(initial, (200, 300, 0)):
    equal(actual, expected, "Initial campaign allocation")
dispatch(first, 200)
dispatch(corporate, 300)
equal(corporate.order_line.qty_delivered, 300, "First corporate shipment")
equal(sum(open_pickings(corporate).move_ids.mapped("product_uom_qty")), 300, "Corporate open balance")

bom = as_user(env["mrp.bom"], planner).create({
    "product_tmpl_id": main.product_tmpl_id.id, "product_id": main.id,
    "product_qty": 1, "product_uom_id": unit.id, "type": "normal",
    "bom_line_ids": [Command.create({"product_id": product.id, "product_qty": 1,
                                     "product_uom_id": unit.id}) for product in (ingredient, packaging)],
})
mo = as_user(env["mrp.production"], planner).create({
    "product_id": main.id, "product_qty": 400, "product_uom_id": unit.id,
    "bom_id": bom.id, "picking_type_id": warehouse.manu_type_id.id,
})
mo.action_confirm()
mo.action_assign()
equal(sum(mo.move_raw_ids.mapped("quantity")), 0, "No material reserved before receipts")
purchases = env["purchase.order"]
for index, product in enumerate((ingredient, packaging)):
    vendor = env["res.partner"].create({"name": f"Synthetic Campaign Supplier {index + 1}", "is_company": True})
    po = as_user(env["purchase.order"], planner).create({
        "partner_id": vendor.id, "picking_type_id": warehouse.in_type_id.id,
        "order_line": [Command.create({
            "product_id": product.id, "name": product.name, "product_qty": 400,
            "product_uom_id": unit.id, "price_unit": 1, "date_planned": planned - timedelta(days=1),
        })],
    })
    po.button_confirm()
    purchases |= po.with_env(env)
delayed = planned + timedelta(days=6)
as_user(purchases[1].order_line, planner).date_planned = delayed
env.invalidate_all()
impacted = corporate.with_env(env)
blocker = impacted.oct_campaign_blocker_id
if (impacted.oct_campaign_status != "supplier_delay" or not blocker
        or not impacted.oct_campaign_next_action or not impacted.oct_campaign_supply_date
        or not blocker.owner_id or not blocker.next_action):
    raise AssertionError("Supplier delay lacks an actionable source-linked campaign blocker.")
if blocker.oct_campaign_order_id != impacted or env["operations.control.item"].search_count([
        ("oct_campaign_order_id", "=", impacted.id)]) != 1:
    raise AssertionError("Supplier-delay blocker does not have a unique originating order link.")
if impacted.oct_campaign_supply_date < delayed.date():
    raise AssertionError("Campaign supply date does not reflect the delayed input.")
blocker_id = blocker.id
count_before = env["operations.control.item"].search_count([])
for unused in range(2):
    as_user(purchases[1].order_line, planner).date_planned = delayed
    reconcile()
    env.invalidate_all()
    if corporate.with_env(env).oct_campaign_blocker_id.id != blocker_id:
        raise AssertionError("Repeated supplier updates replaced the source-linked blocker.")
equal(env["operations.control.item"].search_count([]), count_before, "No duplicate blockers")
passed("supplier_delay_coordination", status_value=impacted.oct_campaign_status,
       blocker_id=blocker_id, source_order_id=corporate.id,
       supply_date=str(impacted.oct_campaign_supply_date), repeated_updates=2)

for po in purchases:
    validate(as_user(po.picking_ids, stock), 400)
    equal(po.order_line.qty_received, 400, "Standard purchase receipt")
mo.action_assign()
for move in mo.move_raw_ids:
    equal(move.quantity, 400, "Reserved manufacturing input")
mo.qty_producing = 400
mo._set_qty_producing()
mo.with_context(skip_redirection=True).button_mark_done()
if mo.state != "done":
    raise AssertionError("Standard manufacturing did not complete.")
equal(mo.qty_produced, 400, "Standard manufactured output")
after_production = [reservation(record) for record in (corporate, last)]
for actual, expected in zip(after_production, (300, 100)):
    equal(actual, expected, "Automatic manufacturing-output allocation")
dispatch(corporate, 200)
equal(sum(open_pickings(corporate).move_ids.mapped("product_uom_qty")), 100, "Repeated corporate balance")
dispatch(corporate, 100)
dispatch(last, 100)
env.invalidate_all()
for record, quantity in ((first, 200), (corporate, 600), (last, 100)):
    equal(record.with_env(env).order_line.qty_delivered, quantity, "Delivered sales quantity")
    if open_pickings(record):
        raise AssertionError("Primary campaign scenario retains open customer demand.")
for product in (main, ingredient, packaging):
    equal(product.qty_available, 0, "Final main-scenario inventory")
passed("role_based_purchase_manufacture_dispatch", initial_stock=500, produced=400,
       dispatched=900, initial_allocation=initial, automatic_allocation=after_production,
       corporate_batches=[300, 200, 100], sales_uid=sales.id, stock_uid=stock.id,
       procurement_manufacturing_uid=planner.id, discount_percent=20, final_main_stock=0)

# A separate product keeps date-negotiation cases independent of the 900-unit case.
product = probe_products["Acceptance"]
seed(product, 1)
early = order(product, 1, "2030-12-15")
late = order(product, 1, "2030-12-20")
pending = proposal(late, "2030-12-10")
equal(reservation(early), 1, "Pending proposal retains allocation")
if not respond(pending, "rejected"):
    raise AssertionError("Rejection was not recorded.")
equal(reservation(early), 1, "Rejected proposal retains allocation")
accepted = proposal(late, "2030-12-10")
if not respond(accepted, "accepted"):
    raise AssertionError("Applicable acceptance did not apply.")
equal(reservation(late), 1, "Acceptance automatically reprioritizes")
equal(reservation(early), 0, "Old allocation reclaimed after acceptance")
if accepted.promise_id.original_date != date(2030, 12, 20) or accepted.promise_id.current_date != date(2030, 12, 10):
    raise AssertionError("Accepted date or original history was lost.")
passed("pending_rejected_and_accepted_dates", original="2030-12-20", accepted="2030-12-10")

# Exercise the real installed scheduler entry without a new cursor/cron service.
product = probe_products["Scheduler"]
seed(product, 1)
scheduler_late = order(product, 1, "2030-12-20")
scheduler_early = order(product, 1, "2030-12-15")
as_user(warehouse.out_type_id, planner).reservation_method = "at_confirm"
(open_pickings(scheduler_early) | open_pickings(scheduler_late)).move_ids._do_unreserve()
equal(reservation(scheduler_early) + reservation(scheduler_late), 0, "Scheduler precondition")
as_user(env["stock.rule"], planner).run_scheduler(use_new_cursor=False, company_id=company.id)
equal(reservation(scheduler_early), 1, "Scheduler date priority")
equal(reservation(scheduler_late), 0, "Scheduler competing demand")
passed("standard_scheduler_entry", use_new_cursor=False, company_id=company.id)

# Commit only guarded synthetic fixtures so genuine independent connections see them.
race_product = probe_products["Supply Race"]
race_late = order(race_product, 1, "2030-12-20")
race_early = order(race_product, 1, "2030-12-15")
accept_product = probe_products["Acceptance Race"]
seed(accept_product, 1)
accept_early = order(accept_product, 1, "2030-12-15")
accept_late = order(accept_product, 1, "2030-12-20")
accept_proposal = proposal(accept_late, "2030-12-10")
phantom_product = probe_products["Order Phantom"]
seed(phantom_product, 1)
phantom_existing = order(phantom_product, 1, "2030-12-20")
line_product = probe_products["Line Phantom"]
line_order = order(line_product, 1, "2030-12-15")
line_proposal = proposal(line_order, "2030-12-20")
preparation_fixtures = []
for path, name in (("move", "Move Preparation Race"), ("raw_line", "Line Preparation Race")):
    product = probe_products[name]
    seed(product, 2)
    prepared_late = order(product, 2, "2030-12-20")
    pending_early = order(product, 1, None)
    equal(reservation(prepared_late), 2, "Preparation initial reservation")
    equal(reservation(pending_early), 0, "Missing-promise competitor remains unallocated")
    preparation_fixtures.append((path, prepared_late, pending_early))

plan_race_fixtures = []
for name in ("Plan Acceptance Race", "Plan Dispatch Race"):
    product = probe_products[name]
    seed(product, 2)
    record = order(product, 2, "2030-12-18")
    model = as_user(env["oct.shipment.plan"], sales)
    offer = model.browse(model.propose(record.id, [
        {"batch": number, "line_id": record.order_line.id, "quantity": 1, "latest_date": "2030-12-18"}
        for number in (1, 2)], "Synthetic race approval"))
    if name == "Plan Dispatch Race":
        offer.respond("accepted", "Synthetic Contact", "email", fields.Datetime.now(), "Synthetic race evidence")
    plan_race_fixtures.append((record, offer))
env.cr.commit()


def sessions(first_cursor, second_cursor):
    first_cursor.execute("SELECT pg_backend_pid()")
    first_pid = first_cursor.fetchone()[0]
    second_cursor.execute("SELECT pg_backend_pid()")
    second_pid = second_cursor.fetchone()[0]
    if first_pid == second_pid:
        raise AssertionError("Campaign race requires distinct PostgreSQL connections.")
    return api.Environment(first_cursor, planner.id, context), api.Environment(second_cursor, planner.id, context), [first_pid, second_pid]


with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    receipt(race_product, 1, a)
    must_refuse(lambda: reconcile(b), "Competing allocation ignored the uncommitted supply mutex.")
    second_cursor.rollback()
    first_cursor.commit()
    b.invalidate_all()
    reconcile(b)
    equal(reservation(race_early, b), 1, "Committed receipt date priority")
    equal(reservation(race_late, b), 0, "No double allocation after receipt")
    second_cursor.commit()
    passed("two_connection_supply_and_allocation", backend_pids=pids, allocated=1, supplied=1)

with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    accepted_row = a["oct.dispatch.proposal"].with_user(sales.id).browse(accept_proposal.id)
    if not respond(accepted_row, "accepted"):
        raise AssertionError("Concurrent date acceptance failed.")
    must_refuse(lambda: reconcile(b), "Allocation raced through uncommitted date acceptance.")
    second_cursor.rollback()
    first_cursor.commit()
    b.invalidate_all()
    reconcile(b)
    equal(reservation(accept_late, b), 1, "Accepted date visible after retry")
    equal(reservation(accept_early, b), 0, "Acceptance retains a single allocation")
    current = b["oct.dispatch.promise"].with_user(sales.id).search([("order_id", "=", accept_late.id)])
    if current.current_date != date(2030, 12, 10):
        raise AssertionError("Accepted date was lost after competing allocation.")
    second_cursor.commit()
    passed("two_connection_acceptance_and_allocation", backend_pids=pids, current_date=str(current.current_date))

for path, prepared_late, pending_early in preparation_fixtures:
    with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
        a, b, pids = sessions(first_cursor, second_cursor)
        picking = open_pickings(prepared_late, a)
        picking.ensure_one()
        move = picking.move_ids
        move.ensure_one()
        equal(move.quantity, 2, "Preparation quantity before concurrent edit")
        if path == "move":
            move.write({"quantity": 1, "picked": True})
        else:
            line = move.move_line_ids
            line.ensure_one()
            line.write({"quantity": 1, "picked": True})
        equal(move.quantity, 1, "Actual uncommitted preparation quantity edit")
        must_refuse(lambda: reconcile(b), "Allocation ignored an uncommitted stock-preparation mutex.")
        second_cursor.rollback()
        first_cursor.commit()
        b.invalidate_all()
        # An earlier promise recorded after preparation may use the newly freed
        # unit, but must not reclaim the already prepared unit.
        b["oct.dispatch.promise"].with_user(sales.id).with_context(**context).establish(
            pending_early.id, "2030-12-15")
        equal(reservation(prepared_late, b), 1, "Prepared unit preserved after competing allocation")
        equal(reservation(pending_early, b), 1, "Released unit allocated to earlier promise")
        prepared = open_pickings(prepared_late, b).move_ids
        if not prepared.picked and not any(prepared.move_line_ids.mapped("picked")):
            raise AssertionError("Allocation lost the prepared state.")
        second_cursor.commit()
        passed("two_connection_preparation_and_allocation", path=path, backend_pids=pids,
               original_reserved=2, prepared_preserved=1, earlier_allocated=1)

with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    # Reading the pool deliberately establishes an earlier REPEATABLE READ snapshot.
    a["oct.campaign.pool"].browse(pool.id).read(["revision"])
    phantom_new = order(phantom_product, 1, "2030-12-10", session=b)
    second_cursor.commit()
    must_refuse(lambda: reconcile(a), "Old allocation snapshot ignored newly inserted earlier demand.")
    first_cursor.rollback()
    a.invalidate_all()
    reconcile(a)
    equal(reservation(phantom_new, a), 1, "Earlier inserted order receives the stock")
    equal(reservation(phantom_existing, a), 0, "Phantom insertion does not double reserve")
    first_cursor.commit()
    passed("repeatable_read_new_order_phantom", backend_pids=pids, allocated=1)

with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    stale = a["oct.dispatch.proposal"].with_user(sales.id).browse(line_proposal.id)
    if stale.is_stale:
        raise AssertionError("Line-phantom proposal starts stale.")
    b["sale.order.line"].with_user(sales.id).create({
        "order_id": line_order.id, "product_id": line_product.id, "name": line_product.name,
        "product_uom_qty": 1, "product_uom_id": unit.id, "price_unit": 10,
    })
    second_cursor.commit()
    must_refuse(lambda: respond(stale, "accepted"), "Old response snapshot ignored a newly inserted order line.")
    first_cursor.rollback()
    a.invalidate_all()
    stale = a["oct.dispatch.proposal"].with_user(sales.id).browse(line_proposal.id)
    if respond(stale, "accepted") or stale.applied or stale.state != "stale":
        raise AssertionError("A changed-scope proposal modified the accepted promise.")
    if stale.promise_id.current_date != date(2030, 12, 15):
        raise AssertionError("Stale response erased the original accepted promise.")
    first_cursor.commit()
    passed("repeatable_read_new_line_phantom", backend_pids=pids, stale_response_applied=False)

accept_order, accept_offer = plan_race_fixtures[0]
with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    offer_a = a["oct.shipment.plan"].with_user(sales.id).browse(accept_offer.id)
    offer_a.respond("accepted", "Synthetic Contact", "email", fields.Datetime.now(), "Synthetic race evidence")
    must_refuse(lambda: validate(open_pickings(accept_order, b), 1),
                "Dispatch ignored uncommitted customer plan acceptance.")
    second_cursor.rollback()
    first_cursor.commit()
    b.invalidate_all()
    validate(open_pickings(accept_order, b), 1)
    delivered = b["sale.order"].with_user(sales.id).browse(accept_order.id).order_line.qty_delivered
    equal(delivered, 1, "One batch dispatched after committed approval")
    second_cursor.commit()
    passed("two_connection_plan_acceptance_and_dispatch", backend_pids=pids, delivered=1)

dispatch_order, dispatch_offer = plan_race_fixtures[1]
with env.registry.cursor() as first_cursor, env.registry.cursor() as second_cursor:
    a, b, pids = sessions(first_cursor, second_cursor)
    validate(open_pickings(dispatch_order, a), 1)
    must_refuse(lambda: validate(open_pickings(dispatch_order, b), 1),
                "Two dispatch transactions consumed the same approved batch.")
    second_cursor.rollback()
    first_cursor.commit()
    b.invalidate_all()
    validate(open_pickings(dispatch_order, b), 1)
    delivered = b["sale.order"].with_user(sales.id).browse(dispatch_order.id).order_line.qty_delivered
    equal(delivered, 2, "Two different approved batches consumed once each")
    second_cursor.commit()
    passed("two_connection_approved_batch_dispatch", backend_pids=pids, delivered=2, approved_batches=2)

env.cr.rollback()
env.invalidate_all()
quants = env["stock.quant"].search([
    ("company_id", "=", company.id), ("location_id", "child_of", warehouse.lot_stock_id.id),
    ("product_id", "in", pool.product_ids.ids),
])
for quant in quants:
    if quant.product_id.uom_id.compare(quant.quantity, 0) < 0:
        raise AssertionError("Campaign probes produced negative stock.")
    if quant.product_id.uom_id.compare(quant.reserved_quantity, quant.quantity) > 0:
        raise AssertionError("Campaign probes reserved the same stock more than once.")
passed("committed_probe_inventory_invariants", checked_quants=len(quants), negative_stock=False, over_reserved=False)

print("OCT_CAMPAIGN_RESULT=" + json.dumps({
    "database": env.cr.dbname, "status": "passed", "cases": results,
    "limitations": [
        "Procurement/MRP planner also has Stock Manager and Manufacturing Administrator rights",
        "Native sales cancellation activity logging is tested with a combined Sales and Stock actor",
        "One company and warehouse; primary manufactured SKU plus isolated probe products",
        "Synthetic opening stock and manually recorded supplier/customer events",
        "Calendar dates in December 2030 do not establish production capacity or real-time SLA",
        "Real independent connections with deliberately interleaved uncommitted transactions, not a load test",
        "No browser rendering, carrier/WMS, authenticated customer consent or formal quality release",
        "Committed synthetic fixtures must be removed with the owned scenario database",
    ],
}, sort_keys=True))
env.cr.rollback()
