from psycopg2.errors import DeadlockDetected, LockNotAvailable, SerializationFailure

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_compare


CONCURRENCY_ERRORS = (DeadlockDetected, LockNotAvailable, SerializationFailure)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    oct_dispatch_guard_revision = fields.Integer(default=0, copy=False, readonly=True)
    oct_dispatch_scope_revision = fields.Integer(default=0, copy=False, readonly=True)
    oct_dispatch_promise_ids = fields.One2many(
        "oct.dispatch.promise", "order_id", string="Warehouse Dispatch Promise", copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        protected = {"oct_dispatch_guard_revision", "oct_dispatch_scope_revision", "oct_dispatch_promise_ids"}
        if any(protected.intersection(vals) for vals in vals_list):
            raise AccessError(_("Dispatch fields can only be changed through the promise workflow."))
        if any(self.env.context.get(f"default_{name}") for name in protected):
            raise AccessError(_("Dispatch field defaults cannot be supplied by a caller."))
        return super().create(vals_list)

    def write(self, vals):
        protected = {"oct_dispatch_guard_revision", "oct_dispatch_scope_revision", "oct_dispatch_promise_ids"}
        if protected.intersection(vals):
            raise AccessError(_("Dispatch fields can only be changed through the promise workflow."))
        if {"state", "date_order", "company_id"}.intersection(vals):
            with self.env.cr.savepoint():
                self._dispatch_lock()
                for order in self:
                    super(SaleOrder, order).write({
                        **vals, "oct_dispatch_scope_revision": order.oct_dispatch_scope_revision + 1,
                    })
            return True
        return super().write(vals)

    def _dispatch_lock(self):
        """Lock/touch protocol; SQL only locks, never writes business data."""
        if not self:
            return
        self.check_access("write")
        try:
            with self.env.cr.savepoint():
                self.flush_recordset()
                self.env.cr.execute(
                    "SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE NOWAIT",
                    (tuple(self.ids),),
                )
                self.env.cr.execute(
                    "SELECT id FROM sale_order_line WHERE order_id IN %s ORDER BY id FOR UPDATE NOWAIT",
                    (tuple(self.ids),),
                )
                self.invalidate_recordset()
                self.order_line.invalidate_recordset()
        except CONCURRENCY_ERRORS as error:
            raise UserError(_("This order changed or is being updated. Refresh and retry.")) from error

    def _dispatch_touch(self, scope=False):
        # Private server method; no context flag or sudo privilege bypass.
        self._dispatch_lock()
        for order in self:
            values = {"oct_dispatch_guard_revision": order.oct_dispatch_guard_revision + 1}
            if scope:
                values["oct_dispatch_scope_revision"] = order.oct_dispatch_scope_revision + 1
            super(SaleOrder, order).write(values)

    def _dispatch_snapshot(self):
        self.ensure_one()
        lines = []
        for line in self.order_line.sorted("id"):
            if line.display_type or not line.product_id or line.product_id.type == "service":
                continue
            lines.append({
                "line_id": line.id, "product_id": line.product_id.id,
                "uom_id": line.product_uom_id.id, "ordered": line.product_uom_qty,
                "delivered": line.qty_delivered,
                "remaining": max(line.product_uom_qty - line.qty_delivered, 0),
                "write_date": fields.Datetime.to_string(line.write_date),
            })
        done_moves = self.env["stock.move"].search([
            ("sale_line_id", "in", [line["line_id"] for line in lines]), ("state", "=", "done"),
        ], order="id")
        return {
            "state": self.state, "date_order": fields.Datetime.to_string(self.date_order),
            "scope_revision": self.oct_dispatch_scope_revision, "lines": lines,
            "done_moves": [{"id": move.id, "quantity": move.quantity,
                            "write_date": fields.Datetime.to_string(move.write_date)} for move in done_moves],
        }

    def _dispatch_has_remaining(self, snapshot):
        return self.state == "sale" and any(
            float_compare(line["remaining"], 0, precision_rounding=self.env["uom.uom"].browse(line["uom_id"]).rounding) > 0
            for line in snapshot["lines"]
        )

    def action_open_dispatch_promise(self):
        self.ensure_one()
        self.check_access("read")
        promise = self.env["oct.dispatch.promise"].search([("order_id", "=", self.id)], limit=1)
        if promise:
            return promise._form_action()
        if not self.env.user.has_group("operations_dispatch_promise.group_dispatch_coordinator"):
            raise AccessError(_("Only a dispatch coordinator can establish a promise."))
        return {
            "type": "ir.actions.act_window", "res_model": "oct.dispatch.wizard", "view_mode": "form",
            "target": "new", "context": {"default_order_id": self.id, "default_operation": "establish"},
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        with self.env.cr.savepoint():
            lines = super().create(vals_list)
            lines.order_id._dispatch_touch(scope=True)
            return lines

    def write(self, vals):
        scope_fields = {"order_id", "product_id", "product_uom_id", "product_uom_qty", "qty_delivered", "display_type"}
        if scope_fields.intersection(vals):
            with self.env.cr.savepoint():
                orders = self.order_id
                result = super().write(vals)
                (orders | self.order_id)._dispatch_touch(scope=True)
                return result
        return super().write(vals)

    def unlink(self):
        with self.env.cr.savepoint():
            orders = self.order_id
            result = super().unlink()
            orders._dispatch_touch(scope=True)
            return result
