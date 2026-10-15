"""Synthetic standard-Odoo observations; run only through validate-fulfilment.ps1.

Executed in Odoo shell with its injected `env`. This diagnostic exercises
standard fields, not the optional promise workflow tested by a separate probe.
All ORM fixtures roll back; the runner also removes the owned DB.
"""

import json
import re
from datetime import datetime, timedelta

from odoo import Command
from odoo.tools.float_utils import float_compare


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname):
    raise RuntimeError("Refusing ORM writes outside a guarded scenario database.")

results = []
unit = env.ref("uom.product_uom_unit")
warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
if not warehouse:
    raise RuntimeError("Missing standard warehouse.")
out_type = warehouse.out_type_id
out_type.write({"reservation_method": "manual", "create_backorder": "always"})
base_date = datetime(2030, 12, 15, 12)
consumer = env["res.partner"].create({"name": "Synthetic Consumer", "is_company": False})
corporate = env["res.partner"].create({"name": "Synthetic Corporate", "is_company": True})


def equal(actual, expected, label):
    if float_compare(actual, expected, precision_digits=5):
        raise AssertionError(f"{label}: expected {expected}, observed {actual}")


def observe(case, status, **evidence):
    results.append({"case": case, "status": status, **evidence})


def product(name):
    return env["product.product"].create({
        "name": f"Synthetic {name}", "type": "consu", "is_storable": True,
        "tracking": "none", "uom_id": unit.id, "sale_delay": 0,
    })


def seed(goods, quantity):
    # Standard ORM fixture helper, not a real purchase/production receipt.
    env["stock.quant"]._update_available_quantity(goods, warehouse.lot_stock_id, quantity)


def sale(goods, quantity, day, business=False, confirmed_day=None):
    order = env["sale.order"].create({
        "partner_id": (corporate if business else consumer).id,
        "warehouse_id": warehouse.id, "picking_policy": "direct" if business else "one",
        "commitment_date": base_date + timedelta(days=day),
        "order_line": [Command.create({
            "product_id": goods.id, "name": goods.name, "product_uom_qty": quantity,
            "product_uom_id": unit.id, "price_unit": 10, "discount": 20,
        })],
    })
    order.action_confirm()
    if confirmed_day is not None:
        # Synthetic historical confirmation timestamp, not real audit evidence.
        order.date_order = base_date - timedelta(days=confirmed_day)
    picking = order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
    picking.ensure_one()
    return order, picking


def reserved(picking):
    return sum(picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel")).mapped("quantity"))


def dispatch(picking, quantity):
    picking.ensure_one()
    moves = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
    moves.ensure_one()
    moves.write({"quantity": quantity, "picked": True})
    action = picking.button_validate()
    if isinstance(action, dict):
        raise AssertionError(f"Unexpected validation wizard: {action.get('res_model')}")
    if picking.state != "done":
        raise AssertionError("Picking did not complete.")
    return env["stock.picking"].search([("backorder_id", "=", picking.id)])


def receive(goods, quantity):
    picking = env["stock.picking"].create({
        "picking_type_id": warehouse.in_type_id.id,
        "location_id": warehouse.in_type_id.default_location_src_id.id,
        "location_dest_id": warehouse.lot_stock_id.id,
        "move_ids": [Command.create({
            "product_id": goods.id, "product_uom_qty": quantity,
            "product_uom": unit.id,
            "location_id": warehouse.in_type_id.default_location_src_id.id,
            "location_dest_id": warehouse.lot_stock_id.id,
        })],
    })
    picking.action_confirm()
    picking.action_assign()
    dispatch(picking, quantity)


try:
    required = {"sale_management", "sale_stock", "purchase_stock", "mrp", "sale_mrp", "operations_control_tower"}
    installed = set(env["ir.module.module"].search([("name", "in", list(required)), ("state", "=", "installed")]).mapped("name"))
    if installed != required:
        raise AssertionError("Required modules are not installed.")
    observe("fresh_standard_install", "pass", modules=sorted(installed))

    goods = product("Campaign SKU")
    components = [product("Ingredient"), product("Packaging")]
    seed(goods, 500)
    bom = env["mrp.bom"].create({
        "product_tmpl_id": goods.product_tmpl_id.id, "product_id": goods.id,
        "product_qty": 1, "product_uom_id": unit.id, "type": "normal",
        "bom_line_ids": [Command.create({"product_id": c.id, "product_qty": 1,
                                         "product_uom_id": unit.id}) for c in components],
    })
    mo = env["mrp.production"].create({
        "product_id": goods.id, "product_qty": 400, "product_uom_id": unit.id,
        "bom_id": bom.id, "picking_type_id": warehouse.manu_type_id.id,
    })
    mo.action_confirm()
    mo.action_assign()
    equal(sum(mo.move_raw_ids.mapped("quantity")), 0, "No inputs reserved before receipts")
    observe("supplier_shortage_visible", "pass", reserved_inputs=0, mo_state=mo.state,
            limitation="Availability observation, not a hard negative-stock prevention test.")
    purchases = env["purchase.order"]
    for index, component in enumerate(components):
        vendor = env["res.partner"].create({"name": f"Synthetic Supplier {index + 1}", "is_company": True})
        po = env["purchase.order"].create({
            "partner_id": vendor.id, "picking_type_id": warehouse.in_type_id.id,
            "order_line": [Command.create({
                "product_id": component.id, "name": component.name, "product_qty": 400,
                "product_uom_id": unit.id, "price_unit": 1, "date_planned": base_date,
            })],
        })
        po.button_confirm()
        purchases |= po
    delayed = base_date + timedelta(days=5)
    purchases[0].order_line.date_planned = delayed
    receipt = purchases[0].picking_ids
    receipt.ensure_one()
    if not receipt.move_ids:
        raise AssertionError("Missing purchase receipt moves.")
    if not all(move.date_deadline == delayed for move in receipt.move_ids):
        raise AssertionError("Supplier delay did not propagate to receipt deadline.")
    observe("supplier_delay", "gap", receipt_deadline=str(delayed),
            missing="No automatic supplier-delay-to-customer-proposal workflow or feasibility guarantee established.")

    # Create in reverse promise order to make date-based manual ordering visible.
    order_c, pick_c = sale(goods, 100, 2)
    order_b, pick_b = sale(goods, 600, 1, business=True)
    order_a, pick_a = sale(goods, 200, 0)
    (pick_c | pick_b | pick_a).action_assign()
    initial_allocation = [reserved(p) for p in (pick_a, pick_b, pick_c)]
    for actual, expected in zip(initial_allocation, (200, 300, 0)):
        equal(actual, expected, "Manual date allocation")
    dispatch(pick_a, 200)
    back_b = dispatch(pick_b, 300)
    back_b.ensure_one()
    equal(sum(back_b.move_ids.mapped("product_uom_qty")), 300, "Corporate balance")
    equal(goods.qty_available, 0, "Finished goods before production")
    for po in purchases:
        dispatch(po.picking_ids, 400)
        equal(po.order_line.qty_received, 400, "Purchased input received")
    mo.action_assign()
    for move in mo.move_raw_ids:
        equal(move.quantity, 400, "Reserved manufacturing input")
    mo.qty_producing = 400
    mo._set_qty_producing()
    action = mo.with_context(skip_redirection=True).button_mark_done()
    if mo.state != "done":
        raise AssertionError(f"Manufacturing incomplete: {action}")
    equal(mo.qty_produced, 400, "Produced finished goods")
    (back_b | pick_c).action_assign()
    back_b2 = dispatch(back_b, 200)
    back_b2.ensure_one()
    equal(sum(back_b2.move_ids.mapped("product_uom_qty")), 100, "Repeated backorder balance")
    dispatch(back_b2, 100)
    dispatch(pick_c, 100)
    for order, expected in ((order_a, 200), (order_b, 600), (order_c, 100)):
        equal(order.order_line.qty_delivered, expected, "Delivered sales quantity")
    equal(goods.qty_available, 0, "Final finished inventory")
    for component in components:
        equal(component.qty_available, 0, "Final component inventory")
    equal(sum(mo.move_raw_ids.mapped("quantity")), 800, "Consumed two inputs")
    remaining = (order_a | order_b | order_c).picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
    if remaining:
        raise AssertionError("Unexpected open customer demand.")
    observe("normal_manufacture_and_corporate_backorders", "pass", initial=500, produced=400,
            dispatched=900, initial_allocation=initial_allocation, corporate_batches=[300, 200, 100],
            customer_delivered=[200, 600, 100], final_stock=0, open_pickings=0)

    priority_goods = product("Priority probe")
    seed(priority_goods, 1)
    _, early = sale(priority_goods, 1, 0)
    _, urgent_late = sale(priority_goods, 1, 2)
    urgent_late.priority = "1"
    (early | urgent_late).action_assign()
    equal(reserved(urgent_late), 1, "Urgency wins over promise date")
    equal(reserved(early), 0, "Earlier promise loses to urgency")
    observe("universal_promise_priority", "gap", early_reserved=0, urgent_late_reserved=1)

    tie_goods = product("Confirmation tie probe")
    seed(tie_goods, 1)
    _, newer_confirmation = sale(tie_goods, 1, 0, confirmed_day=1)
    _, older_confirmation = sale(tie_goods, 1, 0, confirmed_day=2)
    (older_confirmation | newer_confirmation).action_assign()
    equal(reserved(newer_confirmation), 1, "Move order wins over older confirmation")
    equal(reserved(older_confirmation), 0, "Earlier confirmation not selected")
    observe("equal_promise_confirmation_priority", "gap", older_confirmation_reserved=0,
            newer_confirmation_reserved=1, timestamps="Synthetic date_order set after confirmation")

    consumer_goods = product("Consumer partial probe")
    seed(consumer_goods, 1)
    partial_order, partial = sale(consumer_goods, 2, 0)
    partial.action_assign()
    backorder = dispatch(partial, 1)
    backorder.ensure_one()
    equal(partial_order.order_line.qty_delivered, 1, "Consumer partial allowed")
    observe("consumer_complete_dispatch_enforcement", "gap", requested=2, delivered=1,
            picking_policy=partial_order.picking_policy, remaining=1)

    out_type.reservation_method = "at_confirm"
    already_goods = product("Existing reservation probe")
    seed(already_goods, 1)
    _, later_reserved = sale(already_goods, 1, 2)
    _, earlier_unreserved = sale(already_goods, 1, 0)
    (earlier_unreserved | later_reserved).action_assign()
    equal(reserved(later_reserved), 1, "Existing reservation retained")
    equal(reserved(earlier_unreserved), 0, "No automatic reallocation")
    observe("existing_reservation_reallocation", "gap", later_reserved=1, earlier_reserved=0,
            decision="Standard allocation does not implement the approved campaign reallocation policy; tested separately.")

    auto_goods = product("Incoming assignment probe")
    _, late = sale(auto_goods, 1, 2)
    _, first = sale(auto_goods, 1, 0)
    receive(auto_goods, 1)
    allocation = [reserved(first), reserved(late)]
    equal(sum(allocation), 1, "Automatic incoming assignment")
    observe("incoming_automatic_assignment", "observation", allocation_early_late=allocation,
            reservation_method=out_type.reservation_method)

    old_date = partial_order.commitment_date
    new_date = old_date + timedelta(days=3)
    partial_order.commitment_date = new_date
    open_moves = partial_order.picking_ids.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
    if partial_order.commitment_date != new_date or not open_moves:
        raise AssertionError("Standard commitment edit did not persist in transaction.")
    if not all(move.date_deadline == new_date for move in open_moves):
        raise AssertionError("Direct commitment edit did not propagate to open demand.")
    observe("customer_accepted_date_change_gate", "gap", admin_direct_edit_allowed=True,
            open_move_deadline_changed=True,
            missing="No acceptance gate on standard commitment_date; optional promise workflow is tested separately.")
    observe("warehouse_dispatch_semantics", "gap",
            limitation="commitment_date is customer Delivery Date; used only as zero-lead dispatch proxy here.")
    print("OCT_VALIDATION_RESULT=" + json.dumps({
        "database": env.cr.dbname, "status": "observed", "cases": results,
        "scope": "Standard stock and customer Delivery Date behavior, not the optional warehouse-promise workflow",
        "limitations": ["Synthetic admin ORM, one company/warehouse, one main SKU plus isolated probe products",
                        "No UI/carrier/quality test",
                        "Zero product delivery lead, unit BoM, dates fixed in December 2030",
                        "No scheduler run, no supplier delivery event or customer messages",
                        "Known business gaps are not acceptance passes"],
    }, sort_keys=True))
finally:
    env.cr.rollback()
