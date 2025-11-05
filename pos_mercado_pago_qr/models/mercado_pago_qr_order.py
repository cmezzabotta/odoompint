import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PosMercadoPagoQrOrder(models.Model):
    _name = 'pos.mercadopago.qr.order'
    _description = 'Mercado Pago QR Order'
    _order = 'create_date desc'

    name = fields.Char(required=True, index=True, help="Human readable reference for the QR order.")
    payment_method_id = fields.Many2one('pos.payment.method', required=True, ondelete='cascade', index=True)
    pos_session_id = fields.Many2one('pos.session', string='POS Session', index=True)
    order_reference = fields.Char(required=True, index=True, help="POS order name that originated the QR payment request.")
    external_reference = fields.Char(required=True, index=True)
    mercadopago_order_id = fields.Char(index=True, help="Identifier returned by Mercado Pago for the QR order.")
    mercadopago_pos_id = fields.Char(string='Mercado Pago POS ID', help="External POS identifier used when creating the QR order.")
    collector_id = fields.Char(help="Collector (user) identifier on Mercado Pago.")
    amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ], default='pending', required=True, index=True)
    qr_data = fields.Text(help="Raw QR data string returned by Mercado Pago.")
    qr_image = fields.Binary(attachment=True, help="QR image in base64 provided by Mercado Pago.")
    expires_at = fields.Datetime(help="Expiration date of the QR code when provided by Mercado Pago.")
    payload = fields.Text(help="Full JSON payload sent to Mercado Pago when the order was created.")
    last_response = fields.Text(help="Latest JSON payload received from Mercado Pago when polling the order status.")

    @api.model
    def create_from_payload(self, payment_method, payload, response):
        self = self.sudo()
        external_reference = payload.get('external_reference') or ''
        order_reference = external_reference.split('::')[0] if external_reference else payload.get('description')
        order = self.create({
            'name': payload.get('description') or payload.get('title') or external_reference,
            'payment_method_id': payment_method.id,
            'pos_session_id': payment_method.pos_config_ids[:1].current_session_id.id if payment_method.pos_config_ids else False,
            'order_reference': order_reference or external_reference,
            'external_reference': external_reference,
            'mercadopago_order_id': response.get('in_store_order_id'),
            'mercadopago_pos_id': payload.get('pos_id') or payment_method.mpqr_pos_external_id,
            'collector_id': payment_method.mpqr_collector_id,
            'amount': payload['total_amount'],
            'currency_id': payment_method.currency_id.id or payment_method.company_id.currency_id.id,
            'qr_data': response.get('qr_data'),
            'qr_image': response.get('qr_image'),
            'expires_at': response.get('expiration_date'),
            'payload': json.dumps(payload, ensure_ascii=False),
            'last_response': json.dumps(response, ensure_ascii=False),
        })
        _logger.info("Mercado Pago QR order created: %s (%s)", order.id, order.external_reference)
        return order

    def write_from_response(self, response):
        self.ensure_one()
        vals = {
            'last_response': json.dumps(response, ensure_ascii=False),
        }
        status = (response.get('status') or '').lower()
        if status in {'closed', 'finished'}:
            vals['status'] = 'approved'
        elif status in {'rejected', 'cancelled', 'canceled'}:
            vals['status'] = 'rejected'
        elif status in {'expired'}:
            vals['status'] = 'expired'
        elif status in {'open', 'pending', 'in_process'}:
            vals.setdefault('status', 'pending')
        if response.get('qr_data') and not self.qr_data:
            vals['qr_data'] = response['qr_data']
        if response.get('qr_image') and not self.qr_image:
            vals['qr_image'] = response['qr_image']
        if response.get('expiration_date') and not self.expires_at:
            vals['expires_at'] = response['expiration_date']
        super().write(vals)
        _logger.debug("Mercado Pago QR order %s status updated to %s", self.external_reference, self.status)
        return True
