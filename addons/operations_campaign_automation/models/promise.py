from odoo import api, models

from .common import _EVENT_TOKEN


class DispatchPromise(models.Model):
    _inherit = "oct.dispatch.promise"

    @api.model
    def establish(self, order_id, dispatch_date):
        order = self.env["sale.order"].browse(order_id).exists()
        pools = order.oct_campaign_pool_id
        if not pools:
            return super().establish(order_id, dispatch_date)
        order.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(DispatchPromise, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).establish(order_id, dispatch_date)
            pools._campaign_reconcile()
            return result

    def propose(self, proposed_date, reason):
        pools = self.order_id.oct_campaign_pool_id
        if not pools:
            return super().propose(proposed_date, reason)
        with self.env.cr.savepoint():
            self._coordinator_order()
            pools._campaign_lock()
            return super().propose(proposed_date, reason)

    def set_estimate(self, estimate_date):
        pools = self.order_id.oct_campaign_pool_id
        if not pools:
            return super().set_estimate(estimate_date)
        with self.env.cr.savepoint():
            self._coordinator_order()
            pools._campaign_lock()
            return super().set_estimate(estimate_date)


class DispatchProposal(models.Model):
    _inherit = "oct.dispatch.proposal"

    def respond(self, decision, person, channel, response_at, evidence):
        pools = self.order_id.oct_campaign_pool_id
        if not pools:
            return super().respond(decision, person, channel, response_at, evidence)
        self._coordinator_order()
        if decision == "accepted" and self.order_id._shipment_current_plan():
            from odoo.exceptions import UserError
            raise UserError("Use a new quantity-and-date shipment plan to change an accepted batch plan.")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(DispatchProposal, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).respond(
                decision, person, channel, response_at, evidence,
            )
            pools._campaign_reconcile()
            return result
