import hashlib
import hmac
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoQrWebhook(http.Controller):

    @http.route('/mercado-pago/pos-qr/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def mercadopago_qr_webhook(self, **kwargs):
        payload = request.jsonrequest or {}
        if not payload:
            _logger.warning('Mercado Pago QR webhook received an empty payload.')
            return {'status': 'ignored'}

        external_reference = payload.get('external_reference') or payload.get('order', {}).get('external_reference')
        if not external_reference:
            _logger.warning('Mercado Pago QR webhook missing external_reference: %s', payload)
            return {'status': 'ignored'}

        order = request.env['pos.mercadopago.qr.order'].sudo().search([
            ('external_reference', '=', external_reference)
        ], limit=1)
        if not order:
            _logger.info('Mercado Pago QR webhook for unknown reference %s', external_reference)
            return {'status': 'ignored'}

        secret = order.payment_method_id.mpqr_notification_secret
        if secret:
            signature = request.httprequest.headers.get('x-signature') or ''
            if not self._check_signature(signature, secret, request.httprequest.data or b''):
                _logger.warning('Invalid Mercado Pago signature for QR webhook %s', external_reference)
                return request.make_json_response({'status': 'unauthorized'}, status=401)

        order.write_from_response(payload)
        self._notify_pos(order)
        return {'status': 'ok'}

    @staticmethod
    def _check_signature(signature, secret, body):
        if '=' in signature:
            try:
                parts = dict(part.split('=', 1) for part in signature.split(','))
            except ValueError:
                parts = {}
            signature = parts.get('signature') or parts.get('sig') or ''
        digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, digest)

    @staticmethod
    def _notify_pos(order):
        channel = (request.db, 'pos.mercadopago.qr', order.payment_method_id.id)
        request.env['bus.bus'].sudo().sendone(channel, {
            'external_reference': order.external_reference,
            'status': order.status,
        })

