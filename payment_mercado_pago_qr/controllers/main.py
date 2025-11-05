import hmac
import json
import logging
from hashlib import sha256

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoQRController(http.Controller):
    @http.route('/payment/mercado_pago_qr/status/<string:reference>', type='json', auth='public', csrf=False)
    def payment_status(self, reference, **kwargs):
        transaction = request.env['payment.transaction'].sudo().search([
            ('reference', '=', reference),
            ('provider_code', '=', 'mercado_pago_qr'),
        ], limit=1)
        if not transaction:
            return {'state': 'not_found'}
        try:
            transaction._mercado_pago_qr_poll_status()
        except Exception as error:  # noqa: BLE001 - log unexpected polling errors but do not crash checkout
            _logger.exception('Could not poll Mercado Pago status for %s', reference)
            return {'state': transaction.state, 'error': str(error)}
        return {
            'state': transaction.state,
            'mercado_pago_status': transaction.mercado_pago_status,
            'is_post_processed': transaction.is_post_processed,
        }

    @http.route('/payment/mercado_pago_qr/webhook', type='http', auth='public', csrf=False, methods=['POST'])
    def webhook(self, provider_id=None, **kwargs):
        try:
            provider_id = int(provider_id or 0)
        except (TypeError, ValueError):
            provider_id = 0
        provider = request.env['payment.provider'].sudo().browse(provider_id)
        if not provider or provider.code != 'mercado_pago_qr':
            _logger.warning('Mercado Pago webhook received for unknown provider: %s', provider_id)
            return http.Response('provider not found', status=404)

        payload = request.httprequest.get_data() or b''
        signature = request.httprequest.headers.get('X-Signature')
        topic = request.httprequest.args.get('topic') or request.httprequest.args.get('type')

        try:
            data = json.loads(payload.decode('utf-8')) if payload else {}
        except json.JSONDecodeError:
            data = {}

        _logger.debug('Received Mercado Pago webhook: headers=%s payload=%s', request.httprequest.headers, data)

        if signature and provider.mp_webhook_secret:
            topic = topic or data.get('type')
            if not self._validate_signature(provider, signature, payload):
                _logger.warning('Mercado Pago webhook signature mismatch for provider %s. Ignoring notification.', provider.id)
                return http.Response('invalid signature', status=400)

        mp_id = request.httprequest.args.get('id') or data.get('data', {}).get('id') or data.get('id')
        if not mp_id:
            _logger.warning('Mercado Pago webhook without id: %s', data)
            return http.Response('missing id', status=400)

        request.env['payment.transaction'].sudo()._mercado_pago_qr_handle_notification(topic, mp_id, provider)
        return http.Response('ok', status=200)

    def _validate_signature(self, provider, signature, payload):
        try:
            provided = dict(item.split('=') for item in signature.split(','))
        except ValueError:
            return False
        ts = provided.get('ts')
        signature_value = provided.get('v1')
        if not ts or not signature_value:
            return False
        message = f"{ts}.{payload.decode('utf-8')}"
        digest = hmac.new(provider.mp_webhook_secret.encode(), msg=message.encode(), digestmod=sha256).hexdigest()
        return hmac.compare_digest(digest, signature_value)
