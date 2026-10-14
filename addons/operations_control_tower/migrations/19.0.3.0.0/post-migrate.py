from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    items = env["operations.control.item"].search(
        [("reference", "in", [False, "New"])], order="id"
    )
    sequence = env["ir.sequence"]
    for item in items:
        item.reference = (
            sequence.next_by_code("operations.control.item") or "New"
        )
