import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoMezzttController(http.Controller):

    @http.route('/mp/mezztt/create', type='json', auth='user', methods=['POST'])
    def create_qr(self, payment_method_id, amount, currency=None, pos_reference=None, description=None, customer=None):
        payment_method = request.env['pos.payment.method'].browse(int(payment_method_id)).sudo()
        data = {
            'amount': amount,
            'currency': currency,
            'pos_reference': pos_reference,
            'description': description,
            'customer': customer,
            'order_reference': f"{pos_reference or 'POS'}::{request.env.uid}::{payment_method.id}",
        }
        _logger.info('[POS][MP] Creating QR for POS order %s with amount %s', pos_reference, amount)
        response = payment_method.mp_mezztt_create_order(data)
        return response

    @http.route('/mp/mezztt/status', type='json', auth='user', methods=['POST'])
    def poll_status(self, payment_method_id, order_id):
        payment_method = request.env['pos.payment.method'].browse(int(payment_method_id)).sudo()
        _logger.debug('[POS][MP] Poll status -> payment_method=%s order=%s', payment_method.id, order_id)
        return payment_method.mp_mezztt_poll_status(order_id)

    @http.route('/mp/mezztt/cancel', type='json', auth='user', methods=['POST'])
    def cancel(self, payment_method_id, order_id):
        payment_method = request.env['pos.payment.method'].browse(int(payment_method_id)).sudo()
        _logger.info('[POS][MP] Cancel QR -> payment_method=%s order=%s', payment_method.id, order_id)
        payment_method.mp_mezztt_cancel(order_id)
        return {'status': 'cancelled'}

    @http.route('/mp/mezztt/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def webhook(self, **payload):
        signature = request.httprequest.headers.get('X-Webhook-Signature')
        _logger.info('[POS][MP] Webhook received -> %s', payload)
        result = request.env['pos.payment.method'].sudo().mp_mezztt_handle_webhook(payload, signature)
        return result
