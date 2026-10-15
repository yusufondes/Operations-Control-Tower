"""Additional admin configuration checks; savepoint rollback in an owned DB.

Run through odoo shell only after an owner-verified disposable preview starts.
EXPECTED_DATABASE must be injected by the caller. No fixture commit is made.
"""
import json
import re

from odoo import Command
from odoo.exceptions import ValidationError


if not re.fullmatch(r"oct_scenario_[0-9a-f]{32}", env.cr.dbname) or env.cr.dbname != EXPECTED_DATABASE:
    raise RuntimeError("Refusing configuration tests outside the exact owned DB")
if not env.su or not env["ir.module.module"].search_count([
        ("name", "=", "operations_campaign_automation"), ("state", "=", "installed")]):
    raise RuntimeError("Installed campaign and synthetic administrative shell required")


class RollbackCase(Exception):
    pass


results = []


def refused(label, operation):
    try:
        with env.cr.savepoint():
            operation()
    except ValidationError:
        results.append({"case": label, "status": "passed", "expected": "ValidationError"})
        return
    raise AssertionError(label + " unexpectedly succeeded")


try:
    with env.cr.savepoint():
        warehouse = env["stock.warehouse"].create({"name": "Synthetic Configuration Probe", "code": "CVAL"})
        product = env["product.product"].create({
            "name": "Synthetic Configuration Goods", "type": "consu", "is_storable": True, "tracking": "none",
        })
        values = {"name": "Synthetic Configuration Pool", "warehouse_id": warehouse.id,
                  "location_id": warehouse.lot_stock_id.id, "product_ids": [Command.set(product.ids)]}
        for tracking in ("lot", "serial"):
            tracked = env["product.product"].create({
                "name": "Synthetic " + tracking, "type": "consu", "is_storable": True, "tracking": tracking,
            })
            refused("pool_rejects_" + tracking, lambda tracked=tracked: env["oct.campaign.pool"].create({
                **values, "product_ids": [Command.set(tracked.ids)],
            }))
        nonstock = env["product.product"].create({"name": "Synthetic nonstock", "type": "consu", "is_storable": False})
        refused("pool_rejects_nonstorable", lambda: env["oct.campaign.pool"].create({
            **values, "product_ids": [Command.set(nonstock.ids)],
        }))
        refused("pool_rejects_empty_product_scope", lambda: env["oct.campaign.pool"].create({
            **values, "product_ids": [Command.clear()],
        }))
        wrong_location = env["stock.location"].create({"name": "Synthetic Wrong Source", "usage": "internal", "company_id": env.company.id})
        refused("pool_rejects_wrong_stock_source", lambda: env["oct.campaign.pool"].create({**values, "location_id": wrong_location.id}))
        warehouse.delivery_steps = "pick_ship"
        refused("pool_rejects_multi_step_warehouse", lambda: env["oct.campaign.pool"].create(values))
        warehouse.delivery_steps = "ship_only"
        pool = env["oct.campaign.pool"].create(values)
        assert pool.location_id == warehouse.lot_stock_id and pool.product_ids == product
        results.append({"case": "valid_one_step_untracked_pool_succeeds", "status": "passed"})
        raise RollbackCase()
except RollbackCase:
    pass
assert not env["stock.warehouse"].search_count([("code", "=", "CVAL")])
print("OCT_CONFIGURATION_RESULT=" + json.dumps({"database": env.cr.dbname, "status": "passed", "cases": results,
      "fixtures_rolled_back": True, "actor": "synthetic administrative shell, not least-privilege proof"}, sort_keys=True))
env.cr.rollback()
