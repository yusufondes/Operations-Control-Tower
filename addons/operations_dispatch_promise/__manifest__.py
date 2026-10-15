{
    "name": "Operations Dispatch Promise",
    "summary": "Customer-approved warehouse dispatch commitments and response history",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "author": "Yusuf Ondes",
    "license": "LGPL-3",
    "depends": ["sale_stock", "operations_control_tower"],
    "data": [
        "security/dispatch_security.xml",
        "security/ir.model.access.csv",
        "views/dispatch_promise_views.xml",
        "wizard/dispatch_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
