"""Create only synthetic preview fixtures; UI_PASSWORD is injected at runtime."""

import json
import re

from odoo import Command


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname):
    raise RuntimeError("Refusing UI fixtures outside an owned scenario database.")
if not isinstance(UI_PASSWORD, str) or len(UI_PASSWORD) < 24:
    raise RuntimeError("A random disposable UI credential is required.")
coordinator = env["res.users"].create({
    "name": "Synthetic UI Coordinator", "login": "oct.ui.coordinator", "password": UI_PASSWORD,
    "lang": "en_US", "tz": "Europe/Berlin", "company_id": env.company.id,
    "company_ids": [Command.set(env.company.ids)],
    "group_ids": [Command.set([env.ref(name).id for name in (
        "sales_team.group_sale_salesman_all_leads",
        "operations_dispatch_promise.group_dispatch_coordinator",
    )])],
})
customer = env["res.partner"].create({"name": "Synthetic UI Corporate Customer", "is_company": True})
product = env["product.product"].create({
    "name": "Synthetic Campaign UI SKU", "type": "consu", "is_storable": True,
})
order = env["sale.order"].create({
    "partner_id": customer.id, "user_id": coordinator.id, "picking_policy": "direct",
    "commitment_date": "2026-12-14 12:00:00",
    "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 600,
                                    "product_uom_id": product.uom_id.id, "price_unit": 10})],
})
order.action_confirm()
env.cr.commit()
print("OCT_UI_FIXTURE=" + json.dumps({"order_id": order.id, "order_name": order.name,
                                       "user_id": coordinator.id, "login": coordinator.login,
                                       "database": env.cr.dbname}))
