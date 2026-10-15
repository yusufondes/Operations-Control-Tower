from odoo import models, _
from odoo.exceptions import UserError

from .common import _ALLOCATION_TOKEN, _EVENT_TOKEN, internal_event


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        if self.env.context.get("_oct_campaign_allocation_token") is _ALLOCATION_TOKEN:
            return super()._action_assign(force_qty=force_qty)
        pools = self.env["oct.campaign.pool"]._for_moves(self)
        if not pools:
            return super()._action_assign(force_qty=force_qty)
        if not self.env.su and not internal_event(self.env):
            self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            managed = self.filtered(lambda move: bool(move.sale_line_id.order_id.oct_campaign_pool_id)
                                    and move.location_dest_id.usage == "customer")
            for move in managed:
                pool = move.sale_line_id.order_id.oct_campaign_pool_id
                if (move.company_id != pool.company_id or move.location_id != pool.location_id
                        or move.product_id not in pool.product_ids):
                    raise UserError(_("The campaign delivery is outside its configured stock pool."))
            if managed and force_qty:
                raise UserError(_("Forced campaign reservation is unsupported. Reconcile the configured pool."))
            pools._campaign_reconcile()
            outside = self - managed
            if outside:
                return super(StockMove, outside)._action_assign(force_qty=force_qty)
        return None

    def _action_cancel(self):
        if self.env.context.get("_oct_campaign_event_token") is _EVENT_TOKEN:
            return super()._action_cancel()
        pools = self.env["oct.campaign.pool"]._for_moves(self)
        if not pools:
            return super()._action_cancel()
        if not self.env.su and not internal_event(self.env):
            self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(StockMove, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN))._action_cancel()
            pools._campaign_reconcile()
            return result
