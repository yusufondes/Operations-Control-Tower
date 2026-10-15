"""Seed a disposable HALY preview; no physical production or dispatch is inferred.

UI_PASSWORD is injected by preview-dispatch.ps1 and is never included in output.
The initial 500 finished units are synthetic opening inventory, not a receipt.
"""

import json
import re

from odoo import Command
from odoo.tools.float_utils import float_compare


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname):
    raise RuntimeError("Refusing campaign fixtures outside an owned scenario database.")
if not isinstance(UI_PASSWORD, str) or len(UI_PASSWORD) < 24:
    raise RuntimeError("A random disposable UI credential is required.")
module = env["ir.module.module"].search([
    ("name", "=", "operations_campaign_automation"), ("state", "=", "installed"),
])
if len(module) != 1:
    raise RuntimeError("The optional campaign addon must be installed in the owned preview.")

env.company.name = "HALY Synthetic Manufacturing"
coordinator = env["res.users"].create({
    "name": "HALY Synthetic Campaign Coordinator", "login": "oct.ui.campaign",
    "password": UI_PASSWORD, "lang": "en_US", "tz": "Europe/Berlin",
    "company_id": env.company.id, "company_ids": [Command.set(env.company.ids)],
    "group_ids": [Command.set([env.ref(name).id for name in (
        "sales_team.group_sale_salesman_all_leads",
        "operations_dispatch_promise.group_dispatch_coordinator",
        "stock.group_stock_manager",
        "operations_control_tower.group_operations_manager",
    )])],
})


def actor(records):
    return records.with_user(coordinator).with_context(allowed_company_ids=env.company.ids)


warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
if not warehouse or warehouse.delivery_steps != "ship_only":
    raise RuntimeError("The campaign preview requires one standard one-step warehouse.")
actor(warehouse.out_type_id).write({"reservation_method": "manual", "create_backorder": "always"})
unit = env.ref("uom.product_uom_unit")
product = env["product.product"].create({
    "name": "HALY Synthetic Campaign Finished Goods", "type": "consu",
    "is_storable": True, "tracking": "none", "uom_id": unit.id,
})
pool = actor(env["oct.campaign.pool"]).create({
    "name": "HALY Holiday Campaign Pool", "warehouse_id": warehouse.id,
    "location_id": warehouse.lot_stock_id.id,
    "product_ids": [Command.set(product.ids)], "responsible_id": coordinator.id,
})
env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, 500)
specifications = [
    ("A", 200, "consumer", "2026-12-15", False),
    ("B", 600, "corporate", "2026-12-16", True),
    ("C", 100, "consumer", "2026-12-17", False),
]
orders = {}
promises = {}
# Reverse confirmation order makes accepted-date priority observable.
for label, quantity, policy, due, is_company in reversed(specifications):
    customer = env["res.partner"].create({
        "name": f"HALY Synthetic {'Corporate' if is_company else 'Individual'} {label}",
        "is_company": is_company,
    })
    order = actor(env["sale.order"]).create({
        "partner_id": customer.id, "user_id": coordinator.id,
        "warehouse_id": warehouse.id, "picking_policy": "direct",
        "commitment_date": "2026-12-14 12:00:00",
        "oct_campaign_pool_id": pool.id, "oct_campaign_policy": policy,
        "order_line": [Command.create({
            "product_id": product.id, "name": product.name,
            "product_uom_qty": quantity, "product_uom_id": unit.id,
            "price_unit": 10, "discount": 20, "tax_ids": [Command.clear()],
        })],
    })
    order.action_confirm()
    promise_id = actor(env["oct.dispatch.promise"]).establish(order.id, due)
    orders[label] = order
    promises[label] = promise_id

pool.action_reconcile()
allocation = {}
fixtures = {}
for label, quantity, policy, due, _is_company in specifications:
    order = orders[label]
    moves = order.picking_ids.move_ids.filtered(lambda move: move.state not in ("done", "cancel"))
    reserved = sum(move.product_uom._compute_quantity(move.quantity, unit) for move in moves)
    allocation[label] = reserved
    if any(moves.mapped("picked")) or any(order.order_line.mapped("qty_delivered")):
        raise AssertionError("The preview must not prepare or dispatch physical goods.")
    fixtures[label] = {
        "order_id": order.id, "order_name": order.name,
        "picking_ids": order.picking_ids.ids, "promise_id": promises[label],
        "customer_id": order.partner_id.id, "policy": policy,
        "quantity": quantity, "accepted_date": due, "reserved": reserved,
        "status": order.oct_campaign_status,
        "blocker_id": order.oct_campaign_blocker_id.id,
    }
for label, expected in (("A", 200), ("B", 300), ("C", 0)):
    if float_compare(allocation[label], expected, precision_rounding=unit.rounding):
        raise AssertionError(f"Unexpected {label} campaign allocation: {allocation[label]}")
if float_compare(product.qty_available, 500, precision_rounding=unit.rounding):
    raise AssertionError("Synthetic opening inventory unexpectedly changed.")

env.cr.commit()
print("OCT_UI_FIXTURE=" + json.dumps({
    "mode": "campaign", "database": env.cr.dbname,
    "order_id": orders["A"].id, "order_name": orders["A"].name,
    "user_id": coordinator.id, "login": coordinator.login,
    "warehouse_id": warehouse.id, "location_id": warehouse.lot_stock_id.id,
    "pool_id": pool.id, "product_id": product.id,
    "opening_inventory": 500, "allocation": allocation, "orders": fixtures,
    "limitations": ["Synthetic opening inventory, no purchase or manufacturing fixture",
                    "No physical dispatch, production or customer response recorded"],
}, sort_keys=True))
