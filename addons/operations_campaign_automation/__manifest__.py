{
    "name": "HALY Campaign Automation",
    "summary": "Promise-prioritized reservations and complete consumer dispatch",
    "version": "19.0.2.0.0",
    "category": "Inventory",
    "author": "Yusuf Ondes",
    "license": "LGPL-3",
    "depends": ["operations_dispatch_promise", "purchase_stock", "sale_mrp"],
    "data": [
        "security/campaign_security.xml",
        "security/ir.model.access.csv",
        "views/campaign_views.xml",
        "views/shipment_plan_views.xml",
    ],
    "installable": True,
    "application": False,
}
