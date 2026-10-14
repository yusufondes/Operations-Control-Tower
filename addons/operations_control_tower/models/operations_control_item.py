from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OperationsControlItem(models.Model):
    _name = "operations.control.item"
    _description = "Operations Control Item"
    _order = "priority desc, deadline, id"
    _check_company_auto = True

    reference = fields.Char(
        default="New",
        readonly=True,
        copy=False,
        required=True,
        index=True,
    )
    name = fields.Char(required=True, index=True)
    description = fields.Text()
    next_action = fields.Char(string="Next Action")
    owner_id = fields.Many2one(
        "res.users",
        string="Owner",
        default=lambda self: self.env.user,
        required=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    area = fields.Selection(
        [
            ("strategy", "Strategy"),
            ("sales", "Sales"),
            ("procurement", "Procurement"),
            ("production", "Production"),
            ("inventory", "Inventory"),
            ("quality", "Quality"),
            ("logistics", "Logistics"),
            ("maintenance", "Maintenance"),
            ("operations", "Operations"),
            ("finance", "Finance"),
            ("it", "IT & Integrations"),
            ("hr", "People"),
        ],
        default="operations",
        required=True,
        index=True,
    )
    impact = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        default="medium",
        required=True,
        index=True,
    )
    priority = fields.Selection(
        [("0", "Normal"), ("1", "High"), ("2", "Urgent")],
        default="0",
        required=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("waiting_responsible", "Waiting for Responsible"),
            ("waiting_information", "Waiting for Information"),
            ("waiting_third_party", "Waiting for Third Party"),
            ("blocked", "Blocked"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        default="new",
        required=True,
        index=True,
    )
    deadline = fields.Date()
    active = fields.Boolean(default=True)
    is_overdue = fields.Boolean(compute="_compute_is_overdue")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("reference", "New") == "New":
                values["reference"] = (
                    self.env["ir.sequence"].next_by_code(
                        "operations.control.item"
                    )
                    or "New"
                )
        return super().create(vals_list)

    @api.constrains("company_id")
    def _check_company_access(self):
        for item in self:
            if item.company_id not in self.env.companies:
                raise ValidationError(
                    "The control item company must be active for the current user."
                )

    @api.depends("deadline", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for item in self:
            item.is_overdue = bool(
                item.deadline
                and item.deadline < today
                and item.state not in ("resolved", "closed")
            )
