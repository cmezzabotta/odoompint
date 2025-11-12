from odoo import fields, models


class PosMercadoPagoMezzttOrder(models.Model):
    _name = 'pos.mercadopago.mezztt.order'
    _description = 'Mercado Pago POS QR Order (_mezztt)'

    payment_method_id = fields.Many2one('pos.payment.method', required=True, ondelete='cascade')
    pos_order_ref = fields.Char(string='POS Order Reference', index=True)
    external_reference = fields.Char(string='External Reference', required=True, index=True)
    amount = fields.Float(string='Amount', digits='Product Price')
    currency_id = fields.Many2one('res.currency')
    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
            ('error', 'Error'),
        ],
        default='pending',
    )
    mercado_pago_response = fields.Text(string='Last Mercado Pago Response')
    mercado_pago_payment_id = fields.Char(string='Mercado Pago Payment ID', index=True)
