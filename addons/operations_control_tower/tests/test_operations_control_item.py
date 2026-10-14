from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestOperationsControlItem(TransactionCase):
    def test_status_selection(self):
        item = self.env["operations.control.item"].create(
            {"name": "Status selection"}
        )
        self.assertEqual(item.state, "new")

        statuses = [
            "in_progress",
            "waiting_responsible",
            "waiting_information",
            "waiting_third_party",
            "blocked",
            "resolved",
            "closed",
        ]
        for status in statuses:
            item.state = status
            self.assertEqual(item.state, status)

    def test_overdue_flag(self):
        item = self.env["operations.control.item"].create(
            {
                "name": "Late item",
                "deadline": fields.Date.today() - timedelta(days=1),
            }
        )
        self.assertTrue(item.is_overdue)

        item.state = "resolved"
        self.assertFalse(item.is_overdue)

        item.state = "closed"
        self.assertFalse(item.is_overdue)

    def test_defaults_and_reference_sequence(self):
        first_item, second_item = self.env["operations.control.item"].create(
            [{"name": "First item"}, {"name": "Second item"}]
        )

        self.assertEqual(first_item.owner_id, self.env.user)
        self.assertEqual(first_item.company_id, self.env.company)
        self.assertRegex(first_item.reference, r"^OCT/\d{5}$")
        self.assertNotEqual(first_item.reference, second_item.reference)

    def test_operations_business_areas(self):
        areas = [
            "procurement",
            "production",
            "inventory",
            "quality",
            "logistics",
            "maintenance",
        ]
        for area in areas:
            item = self.env["operations.control.item"].create(
                {"name": f"{area.title()} scenario", "area": area}
            )
            self.assertEqual(item.area, area)
