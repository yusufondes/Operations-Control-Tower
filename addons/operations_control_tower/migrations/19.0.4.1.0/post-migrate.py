from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Item = env["operations.control.item"]
    Item.search([]).write({"state": "closed"})

    today = fields.Date.today()
    scenarios = [
        {
            "name": "Reconcile WMS and Odoo stock for Hydration Lemon tubs",
            "area": "inventory",
            "impact": "critical",
            "priority": "2",
            "state": "in_progress",
            "deadline": today + timedelta(days=2),
            "next_action": "Review the 42-unit variance with warehouse operations",
            "description": "Fictional portfolio scenario: compare the warehouse snapshot with Odoo stock and document the root cause of the variance.",
        },
        {
            "name": "Release Energy sample box batch after quality review",
            "area": "quality",
            "impact": "high",
            "priority": "1",
            "state": "waiting_information",
            "deadline": today + timedelta(days=1),
            "next_action": "Confirm the laboratory result and record the release decision",
            "description": "Fictional portfolio scenario: keep the batch on review until all required quality results are available.",
        },
        {
            "name": "Confirm delivery date for natural flavour blend",
            "area": "procurement",
            "impact": "high",
            "priority": "1",
            "state": "waiting_third_party",
            "deadline": today + timedelta(days=3),
            "next_action": "Obtain a confirmed delivery date from the ingredient supplier",
            "description": "Fictional portfolio scenario: monitor a supplier commitment that affects the next powder blending schedule.",
        },
        {
            "name": "Investigate sachet seal integrity deviation",
            "area": "production",
            "impact": "critical",
            "priority": "2",
            "state": "blocked",
            "deadline": today + timedelta(days=1),
            "next_action": "Run a controlled seal-temperature trial on the packing line",
            "description": "Fictional portfolio scenario: isolate the affected sample and verify packaging parameters before production resumes.",
        },
        {
            "name": "Calibrate the powder filling line before the next run",
            "area": "maintenance",
            "impact": "high",
            "priority": "1",
            "state": "waiting_responsible",
            "deadline": today + timedelta(days=5),
            "next_action": "Assign a maintenance owner and confirm the calibration window",
            "description": "Fictional portfolio scenario: complete preventive calibration before the next scheduled production batch.",
        },
        {
            "name": "Prepare carrier handover for Iced Tea sample boxes",
            "area": "logistics",
            "impact": "medium",
            "priority": "0",
            "state": "new",
            "deadline": today + timedelta(days=4),
            "next_action": "Verify carton count, labels, and carrier collection slot",
            "description": "Fictional portfolio scenario: coordinate the outbound handover for a sample-box shipment.",
        },
        {
            "name": "Review the reorder point for electrolyte premix",
            "area": "inventory",
            "impact": "high",
            "priority": "1",
            "state": "in_progress",
            "deadline": today + timedelta(days=7),
            "next_action": "Compare demand coverage with supplier lead time",
            "description": "Fictional portfolio scenario: adjust the replenishment threshold to reduce production shortage risk.",
        },
        {
            "name": "Resolve the missing certificate for Milkshake base powder",
            "area": "quality",
            "impact": "critical",
            "priority": "2",
            "state": "waiting_third_party",
            "deadline": today + timedelta(days=2),
            "next_action": "Request the signed certificate of analysis from the supplier",
            "description": "Fictional portfolio scenario: prevent material release until the required supplier document is available.",
        },
        {
            "name": "Validate retry handling for WMS stock updates",
            "area": "it",
            "impact": "high",
            "priority": "1",
            "state": "new",
            "deadline": today + timedelta(days=8),
            "next_action": "Simulate a failed stock message and verify safe reprocessing",
            "description": "Fictional portfolio scenario: confirm that integration retries do not create duplicate inventory movements.",
        },
        {
            "name": "Approve stock readiness for a seasonal flavour launch",
            "area": "strategy",
            "impact": "medium",
            "priority": "0",
            "state": "resolved",
            "deadline": today + timedelta(days=14),
            "next_action": "Record management sign-off and close after handover",
            "description": "Fictional portfolio scenario: summarize ingredient, packaging, and finished-goods readiness for launch approval.",
        },
    ]
    Item.create(scenarios)
