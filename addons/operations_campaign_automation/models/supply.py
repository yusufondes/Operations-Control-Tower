from odoo import api, fields, models
from odoo.exceptions import AccessError

from .common import _EVENT_TOKEN, internal_event


class CampaignPool(models.Model):
    _inherit = "oct.campaign.pool"

    @api.model
    def _for_supply_products(self, products, companies):
        if any(company not in self.env.companies for company in companies):
            raise AccessError("Supply event company is not active.")
        if not products or not companies:
            return self.browse()
        bom_lines = self.env["mrp.bom.line"].sudo().search([
            ("product_id", "in", products.ids), "|", ("bom_id.company_id", "=", False),
            ("bom_id.company_id", "in", companies.ids),
        ])
        finished = self.env["product.product"]
        for bom in bom_lines.bom_id:
            finished |= bom.product_id or bom.product_tmpl_id.product_variant_ids
        return self.with_context(active_test=False).search([
            ("company_id", "in", companies.ids), ("product_ids", "in", (products | finished).ids),
        ])

    def _campaign_supply_risk_date(self, products, promise_date):
        self.ensure_one()
        productions = self.env["mrp.production"].sudo().search([
            ("company_id", "=", self.company_id.id), ("product_id", "in", products.ids),
            ("state", "not in", ["done", "cancel"]),
        ])
        components = productions.move_raw_ids.filtered(lambda move: move.state not in ("done", "cancel")).product_id
        if not components:
            return False
        purchases = self.env["purchase.order.line"].sudo().search([
            ("company_id", "=", self.company_id.id), ("product_id", "in", components.ids),
            ("order_id.state", "in", ["purchase", "done"]),
        ])
        late = [fields.Date.to_date(line.date_planned) for line in purchases
                if line.product_qty > line.qty_received and line.date_planned
                and fields.Date.to_date(line.date_planned) > promise_date]
        return max(late) if late else False


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def write(self, values):
        if not {"date_planned", "product_qty", "product_id", "order_id"}.intersection(values) or internal_event(self.env):
            return super().write(values)
        self.check_access("write")
        products = self.product_id | self.env["product.product"].browse(values.get("product_id") or [])
        pools = self.env["oct.campaign.pool"]._for_supply_products(products, self.company_id)
        if not pools:
            return super().write(values)
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(PurchaseOrderLine, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).write(values)
            pools._campaign_reconcile()
            return result


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        self.check_access("write")
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.order_line.product_id, self.company_id)
        if not pools:
            return super().button_confirm()
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(PurchaseOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).button_confirm()
            pools._campaign_reconcile()
            return result

    def button_cancel(self):
        self.check_access("write")
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.order_line.product_id, self.company_id)
        if not pools:
            return super().button_cancel()
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(PurchaseOrder, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).button_cancel()
            pools._campaign_reconcile()
            return result


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model_create_multi
    def create(self, vals_list):
        products = self.env["product.product"].browse(sorted({values["product_id"] for values in vals_list if values.get("product_id")}))
        companies = self.env["res.company"].browse(sorted({values.get("company_id") or self.env.company.id for values in vals_list}))
        pools = self.env["oct.campaign.pool"]._for_supply_products(products, companies)
        if not pools:
            return super().create(vals_list)
        self.check_access("create")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            records = super(MrpProduction, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).create(vals_list)
            pools._campaign_reconcile()
            return records.with_env(self.env)

    def write(self, values):
        if internal_event(self.env) or not {"state", "date_start", "date_finished", "date_deadline", "product_qty", "product_id"}.intersection(values):
            return super().write(values)
        self.check_access("write")
        products = self.product_id | self.env["product.product"].browse(values.get("product_id") or [])
        pools = self.env["oct.campaign.pool"]._for_supply_products(products, self.company_id)
        if not pools:
            return super().write(values)
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(MrpProduction, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).write(values)
            pools._campaign_reconcile()
            return result

    def action_confirm(self):
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.product_id, self.company_id)
        if not pools:
            return super().action_confirm()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(MrpProduction, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).action_confirm()
            pools._campaign_reconcile()
            return result

    def action_assign(self):
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.product_id, self.company_id)
        if not pools:
            return super().action_assign()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(MrpProduction, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).action_assign()
            pools._campaign_reconcile()
            return result

    def button_mark_done(self):
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.product_id, self.company_id)
        if not pools:
            return super().button_mark_done()
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(MrpProduction, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN)).button_mark_done()
            pools._campaign_reconcile()
            return result


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        pools = self.env["oct.campaign.pool"]._for_supply_products(self.product_id, self.company_id)
        if not pools or internal_event(self.env):
            return super()._action_done(cancel_backorder=cancel_backorder)
        self.check_access("write")
        with self.env.cr.savepoint():
            pools._campaign_lock()
            result = super(StockMove, self.with_context(_oct_campaign_event_token=_EVENT_TOKEN))._action_done(cancel_backorder=cancel_backorder)
            pools._campaign_reconcile()
            return result.with_env(self.env)
