from odoo import fields, models, _
from odoo.exceptions import UserError


class ShipmentPlanWizard(models.TransientModel):
    _name = "oct.shipment.plan.wizard"
    _description = "Propose or Record Customer Shipment Plan Response"

    operation = fields.Selection([("propose", "Propose"), ("respond", "Record response")], required=True, default="propose")
    order_id = fields.Many2one("sale.order", required=True)
    plan_id = fields.Many2one("oct.shipment.plan")
    row_ids = fields.One2many("oct.shipment.plan.wizard.row", "wizard_id")
    reason = fields.Text()
    decision = fields.Selection([("accepted", "Accepted"), ("rejected", "Rejected")])
    person = fields.Char(string="Customer Contact")
    channel = fields.Selection([("email", "Email reference"), ("phone", "Phone note"), ("other", "Other reference")])
    response_at = fields.Datetime(default=fields.Datetime.now)
    evidence = fields.Text(string="Response Evidence")

    def action_apply(self):
        self.ensure_one()
        self.order_id.check_access("write")
        if self.operation == "propose":
            plan = self.env["oct.shipment.plan"].browse(self.env["oct.shipment.plan"].propose(self.order_id.id, [
                {"batch": row.batch, "line_id": row.sale_line_id.id, "quantity": row.quantity, "latest_date": row.latest_date}
                for row in self.row_ids], self.reason))
        else:
            plan = self.plan_id
            if not plan or plan.order_id != self.order_id:
                raise UserError(_("The response must belong to this order's shipment plan."))
            plan.respond(self.decision, self.person, self.channel, self.response_at, self.evidence)
        return {"type": "ir.actions.act_window", "res_model": "oct.shipment.plan", "res_id": plan.id, "view_mode": "form"}


class ShipmentPlanWizardRow(models.TransientModel):
    _name = "oct.shipment.plan.wizard.row"
    _description = "Proposed Shipment Batch Quantity"

    wizard_id = fields.Many2one("oct.shipment.plan.wizard", required=True, ondelete="cascade")
    batch = fields.Integer(required=True, default=1)
    sale_line_id = fields.Many2one("sale.order.line", required=True)
    quantity = fields.Float(required=True, digits="Product Unit")
    latest_date = fields.Date(required=True, string="Latest Dispatch Date")
