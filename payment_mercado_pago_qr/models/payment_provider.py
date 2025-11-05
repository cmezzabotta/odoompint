import logging
import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


MERCADO_PAGO_API_URL = 'https://api.mercadopago.com'


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('mercado_pago_qr', 'Mercado Pago QR')], ondelete={'mercado_pago_qr': 'set default'})
    mp_access_token = fields.Char(
        string='Access token',
        help='Mercado Pago access token in production mode',
        groups='payment.group_payment_manager'
    )
    mp_collector_id = fields.Char(
        string='Collector ID',
        help='Collector (user) ID associated with the Mercado Pago account',
        groups='payment.group_payment_manager'
    )
    mp_pos_id = fields.Char(
        string='Store POS ID',
        help='Store POS identifier configured on Mercado Pago QR section',
        groups='payment.group_payment_manager'
    )
    mp_external_pos_id = fields.Char(
        string='External POS ID',
        help='External POS identifier registered in Mercado Pago',
        groups='payment.group_payment_manager'
    )
    mp_webhook_secret = fields.Char(
        string='Webhook secret',
        help='Secret shared with Mercado Pago to validate webhook signatures',
        groups='payment.group_payment_manager'
    )
    mp_notification_url = fields.Char(
        string='Notification URL',
        compute='_compute_mp_notification_url',
        groups='payment.group_payment_manager'
    )

    def _mercado_pago_make_request(self, method, endpoint, payload=None, params=None):
        self.ensure_one()
        headers = {
            'Authorization': f'Bearer {self.mp_access_token}',
            'Content-Type': 'application/json',
        }
        url = f"{MERCADO_PAGO_API_URL}{endpoint}"
        _logger.debug('Mercado Pago request: %s %s payload=%s params=%s', method, url, payload, params)
        request_kwargs = {
            'headers': headers,
            'params': params,
            'timeout': 20,
        }
        if payload is not None:
            request_kwargs['json'] = payload
        try:
            response = requests.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as err:
            _logger.exception('Mercado Pago responded with an error: %s', err)
            message = err.response.json() if err.response and err.response.content else {}
            raise ValidationError(_('Mercado Pago error: %s') % message) from err
        except requests.exceptions.RequestException as err:
            _logger.exception('Could not reach Mercado Pago: %s', err)
            raise ValidationError(_('Could not reach Mercado Pago. Please verify your credentials.')) from err

    def _mercado_pago_notification_url(self):
        self.ensure_one()
        base = self.get_base_url()
        return f"{base}/payment/mercado_pago_qr/webhook?provider_id={self.id}"

    def _compute_mp_notification_url(self):
        for provider in self:
            if provider.code == 'mercado_pago_qr' and provider.id:
                provider.mp_notification_url = provider._mercado_pago_notification_url()
            else:
                provider.mp_notification_url = False

    def _mercado_pago_create_preference(self, tx, notification_url=None):
        self.ensure_one()
        amount = tx.amount
        currency = tx.currency_id.name
        payload = {
            'external_reference': tx.reference,
            'notification_url': notification_url,
            'statement_descriptor': tx.company_id.name[:22] if tx.company_id.name else 'Odoo',
            'items': [
                {
                    'title': tx.reference,
                    'description': tx.reference,
                    'currency_id': currency,
                    'category_id': 'others',
                    'quantity': 1,
                    'unit_price': amount,
                }
            ],
            'purpose': 'wallet_purchase',
            'payment_methods': {
                'excluded_payment_types': [{'id': 'ticket'}, {'id': 'atm'}],
            },
            'metadata': {
                'odoo_transaction_id': tx.id,
                'odoo_reference': tx.reference,
            },
        }
        if self.mp_pos_id:
            payload['pos_id'] = self.mp_pos_id
        if self.mp_external_pos_id:
            payload['external_pos_id'] = self.mp_external_pos_id
        if self.mp_collector_id:
            try:
                payload['collector_id'] = int(self.mp_collector_id)
            except ValueError as err:
                raise ValidationError(_('Collector ID must be a number.')) from err
        response = self._mercado_pago_make_request('POST', '/checkout/preferences', payload)
        _logger.debug('Mercado Pago preference response: %s', response)
        return response
