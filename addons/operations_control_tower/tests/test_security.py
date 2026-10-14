from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestOperationsControlSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_group = cls.env.ref(
            "operations_control_tower.group_operations_user"
        )
        manager_group = cls.env.ref(
            "operations_control_tower.group_operations_manager"
        )
        company = cls.env.company
        cls.other_company = cls.env["res.company"].create(
            {"name": "Operations Test Secondary Company"}
        )
        common_values = {
            "company_id": company.id,
            "company_ids": [Command.set([company.id])],
        }
        cls.operations_user = cls.env["res.users"].create(
            {
                **common_values,
                "name": "Operations Test User",
                "login": "operations_test_user",
                "group_ids": [Command.set([user_group.id])],
            }
        )
        cls.operations_manager = cls.env["res.users"].create(
            {
                **common_values,
                "name": "Operations Test Manager",
                "login": "operations_test_manager",
                "group_ids": [Command.set([manager_group.id])],
            }
        )
        cls.other_company_user = cls.env["res.users"].sudo().create(
            {
                "name": "Secondary Company User",
                "login": "operations_secondary_company_user",
                "company_id": cls.other_company.id,
                "company_ids": [Command.set([cls.other_company.id])],
                "group_ids": [Command.set([user_group.id])],
            }
        )
        cls.Item = cls.env["operations.control.item"]

    def test_user_sees_only_assigned_items(self):
        own_item = self.Item.with_user(self.operations_user).create(
            {"name": "User-owned item"}
        )
        manager_item = self.Item.with_user(self.operations_manager).create(
            {"name": "Manager-owned item"}
        )

        visible_items = self.Item.with_user(self.operations_user).search(
            [("id", "in", [own_item.id, manager_item.id])]
        )
        self.assertEqual(visible_items, own_item)

        with self.assertRaises(AccessError):
            self.Item.with_user(self.operations_user).browse(manager_item.id).read(
                ["name"]
            )

    def test_manager_sees_all_company_items(self):
        user_item = self.Item.with_user(self.operations_user).create(
            {"name": "Assigned item"}
        )
        manager_item = self.Item.with_user(self.operations_manager).create(
            {"name": "Portfolio item"}
        )

        visible_items = self.Item.with_user(self.operations_manager).search(
            [("id", "in", [user_item.id, manager_item.id])]
        )
        self.assertEqual(set(visible_items.ids), {user_item.id, manager_item.id})

    def test_only_manager_can_delete_items(self):
        item = self.Item.with_user(self.operations_user).create(
            {"name": "Protected item"}
        )

        with self.assertRaises(AccessError):
            item.with_user(self.operations_user).unlink()

        item.with_user(self.operations_manager).unlink()
        self.assertFalse(item.exists())

    def test_company_boundary_is_enforced(self):
        own_item = self.Item.with_user(self.operations_user).create(
            {"name": "Primary company item"}
        )
        other_item = (
            self.Item.sudo()
            .with_context(allowed_company_ids=[self.other_company.id])
            .create(
                {
                    "name": "Secondary company item",
                    "company_id": self.other_company.id,
                    "owner_id": self.other_company_user.id,
                }
            )
        )

        with self.assertRaises(UserError):
            own_item.with_user(self.operations_user).write(
                {
                    "company_id": self.other_company.id,
                    "owner_id": self.other_company_user.id,
                }
            )

        visible_items = self.Item.with_user(self.operations_manager).search(
            [("id", "in", [own_item.id, other_item.id])]
        )
        self.assertEqual(visible_items, own_item)
