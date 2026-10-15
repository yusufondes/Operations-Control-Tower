from odoo import fields, models, _
from odoo.exceptions import AccessError, UserError


class DispatchWizard(models.TransientModel):
    _name = "oct.dispatch.wizard"
    _description = "Record Dispatch Promise or Customer Response"

    operation = fields.Selection([
        ("establish", "Establish Original Promise"), ("propose", "Propose New Date"),
        ("estimate", "Update Operational Estimate"), ("respond", "Record Customer Response"),
    ], required=True, default="establish")
    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    promise_id = fields.Many2one("oct.dispatch.promise", readonly=True)
    proposal_id = fields.Many2one("oct.dispatch.proposal", readonly=True)
    dispatch_date = fields.Date(string="Warehouse Dispatch Date")
    reason = fields.Text()
    decision = fields.Selection([("accepted", "Accepted"), ("rejected", "Rejected")])
    response_person = fields.Char(string="Customer Respondent")
    response_channel = fields.Selection([("email", "Email reference"), ("phone", "Phone note"), ("other", "Other reference")])
    response_at = fields.Datetime(string="Customer Response Time", default=fields.Datetime.now)
    response_evidence = fields.Text(string="Synthetic Response Evidence")

    def action_apply(self):
        self.ensure_one()
        self.check_access("write")
        if not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can apply this workflow."))
        self.order_id.check_access("write")
        if self.operation == "establish":
            promise_id = self.env["oct.dispatch.promise"].establish(self.order_id.id, self.dispatch_date)
            return self.env["oct.dispatch.promise"].browse(promise_id)._form_action()
        if not self.promise_id or self.promise_id.order_id != self.order_id:
            raise UserError(_("The promise does not match the selected sales order."))
        if self.operation == "propose":
            self.promise_id.propose(self.dispatch_date, self.reason)
        elif self.operation == "estimate":
            self.promise_id.set_estimate(self.dispatch_date)
        elif self.operation == "respond":
            if not self.proposal_id or self.proposal_id.promise_id != self.promise_id:
                raise UserError(_("The proposal does not match the selected promise."))
            applied = self.proposal_id.respond(self.decision, self.response_person, self.response_channel,
                                               self.response_at, self.response_evidence)
            if not applied:
                return {
                    "type": "ir.actions.client", "tag": "display_notification",
                    "params": {"title": _("Response retained, not applied"),
                               "message": _("The proposal is stale. The current promise is unchanged."),
                               "sticky": True, "type": "warning", "next": self.promise_id._form_action()},
                }
        else:
            raise UserError(_("Unknown dispatch operation."))
        return self.promise_id._form_action()
