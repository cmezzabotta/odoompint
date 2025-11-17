from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    fiscal_invoice_requested = fields.Boolean(
        string="Fiscal Ticket Requested",
        help="Indicates that the cashier explicitly requested the fiscal "
        "invoice/ticket when confirming the order."
    )

    @classmethod
    def _order_fields(cls, ui_order):
        vals = super()._order_fields(ui_order)
        vals["fiscal_invoice_requested"] = ui_order.get("fiscal_invoice_requested", False)
        return vals

    @classmethod
    def _process_order(cls, order, draft, existing_order):
        # Preserve what the cashier selected so the printed receipt can reflect it,
        # but always generate the backend invoice to keep accounting in sync.
        original_to_invoice = order.get("to_invoice", False)
        order = dict(order)
        order["fiscal_invoice_requested"] = original_to_invoice
        order["to_invoice"] = True
        return super()._process_order(order, draft, existing_order)
