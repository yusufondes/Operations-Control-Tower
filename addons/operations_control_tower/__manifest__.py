{
    "name": "Operations Control Tower 2.0",
    "summary": "A lightweight operations control center for portfolio projects",
    "version": "19.0.4.1.0",
    "category": "Operations",
    "author": "Yusuf Ondes",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/operations_control_security.xml",
        "security/ir.model.access.csv",
        "data/operations_control_sequence.xml",
        "views/operations_control_item_views.xml",
    ],
    "demo": [
        "demo/operations_control_item_demo.xml",
    ],
    "application": True,
    "installable": True,
}
