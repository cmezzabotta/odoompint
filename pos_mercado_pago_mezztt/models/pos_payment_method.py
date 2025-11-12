import json
import logging
from uuid import uuid4

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import mp_config
from .mp_client import MercadoPagoMezzttClient

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    mp_mezztt_enabled = fields.Boolean(string='Mercado Pago QR (_mezztt)', help='Enable Mercado Pago QR (_mezztt) integration.')
    mp_mezztt_provider_id = fields.Many2one(
        'payment.provider',
        string='Mercado Pago Provider',
        help='Select the Mercado Pago (Pago Online) provider to reuse its credentials.',
    )
    mp_mezztt_last_error = fields.Text(string='Mercado Pago (_mezztt) Last Error', readonly=True)
    mp_mezztt_last_reference = fields.Char(string='Last External Reference', readonly=True)

    def _get_payment_terminal_selection(self):
        selection = list(super()._get_payment_terminal_selection())
        entry = ('mercado_pago_qr_mezztt', 'Mercado Pago QR (_mezztt)')
        if entry not in selection:
            selection.append(entry)
        return selection

    @api.depends('mp_mezztt_enabled')
    def _compute_type(self):
        super()._compute_type()
        for method in self:
            if method.mp_mezztt_enabled and method.type != 'qr_code':
                method.type = 'qr_code'

    def write(self, vals):
        vals = dict(vals)
        if vals.get('use_payment_terminal') == 'mercado_pago_qr_mezztt':
            vals.setdefault('mp_mezztt_enabled', True)
        res = super().write(vals)
        if 'mp_mezztt_enabled' in vals or vals.get('use_payment_terminal') == 'mercado_pago_qr_mezztt':
            for method in self:
                if method.mp_mezztt_enabled:
                    method.with_context(pos_skip_terminal_sync=True).write({
                        'use_payment_terminal': 'mercado_pago_qr_mezztt',
                        'payment_method_type': 'terminal',
                    })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get('use_payment_terminal') == 'mercado_pago_qr_mezztt':
                vals.setdefault('mp_mezztt_enabled', True)
            cleaned.append(vals)
        methods = super().create(cleaned)
        for method, vals in zip(methods, cleaned):
            if vals.get('mp_mezztt_enabled') or vals.get('use_payment_terminal') == 'mercado_pago_qr_mezztt':
                method.with_context(pos_skip_terminal_sync=True).write({
                    'use_payment_terminal': 'mercado_pago_qr_mezztt',
                    'payment_method_type': 'terminal',
                })
        return methods

    def _mp_mezztt_get_provider(self):
        self.ensure_one()
        provider = self.mp_mezztt_provider_id
        if provider:
            return provider.sudo()
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'mercado_pago')
        ], limit=1)
        return provider

    def _mp_mezztt_credentials(self):
        self.ensure_one()
        provider = self._mp_mezztt_get_provider()
        access_token = None
        public_key = None
        if provider:
            for field_name in ('mercado_pago_access_token', 'mp_access_token', 'access_token'):
                access_token = getattr(provider, field_name, None) or access_token
            for field_name in ('mercado_pago_public_key', 'mp_public_key', 'public_key'):
                public_key = getattr(provider, field_name, None) or public_key
        access_token = access_token or mp_config.MP_ACCESS_TOKEN
        public_key = public_key or mp_config.MP_PUBLIC_KEY
        if not access_token:
            raise UserError(_('The Mercado Pago access token is not configured.'))
        if not public_key:
            _logger.warning('Mercado Pago public key not found; continuing with hardcoded value.')
        return {
            'access_token': access_token,
            'public_key': public_key,
            'collector_id': mp_config.COLLECTOR_ID,
            'pos_id': mp_config.POS_ID,
            'terminal_id': mp_config.TERMINAL_ID,
            'store_id': mp_config.STORE_ID,
        }

    def _mp_mezztt_client(self):
        creds = self._mp_mezztt_credentials()
        return creds, MercadoPagoMezzttClient(creds['access_token'])

    def mp_mezztt_prepare_order(self, amount, currency_name, order_reference, description=None, customer=None):
        self.ensure_one()
        if amount <= 0:
            raise UserError(_('The amount to charge must be positive.'))
        description = description or (_('POS Order %s') % order_reference)
        customer = customer or {}
        payload = {
            'external_reference': order_reference,
            'total_amount': round(amount, 2),
            'description': description,
            'title': description,
            'notification_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url', '') + '/mp/mezztt/webhook',
            'items': [
                {
                    'title': description,
                    'unit_price': round(amount, 2),
                    'quantity': 1,
                    'unit_measure': 'unit',
                    'total_amount': round(amount, 2),
                }
            ],
        }
        if currency_name:
            payload['currency_id'] = currency_name
        email = customer.get('email') if isinstance(customer, dict) else None
        name = customer.get('name') if isinstance(customer, dict) else None
        payload['additional_info'] = {
            'external_reference': order_reference,
            'buyer': {
                'email': email,
                'first_name': name,
            }
        }
        return payload

    def mp_mezztt_create_order(self, data):
        self.ensure_one()
        if not self.mp_mezztt_enabled:
            raise UserError(_('The payment method is not configured for Mercado Pago QR (_mezztt).'))
        creds, client = self._mp_mezztt_client()
        order_reference = data.get('order_reference') or f"POS-{uuid4()}"
        payload = self.mp_mezztt_prepare_order(
            amount=float(data['amount']),
            currency_name=data.get('currency'),
            order_reference=order_reference,
            description=data.get('description'),
            customer=data.get('customer'),
        )
        response = client.create_qr(creds['collector_id'], creds['pos_id'], creds['terminal_id'], payload)
        order_vals = {
            'payment_method_id': self.id,
            'pos_order_ref': data.get('pos_reference'),
            'external_reference': order_reference,
            'amount': payload['total_amount'],
            'currency_id': self.currency_id.id or self.company_id.currency_id.id,
            'status': 'pending',
            'mercado_pago_response': json.dumps(response),
        }
        order = self.env['pos.mercadopago.mezztt.order'].sudo().create(order_vals)
        self.write({
            'mp_mezztt_last_error': False,
            'mp_mezztt_last_reference': order.external_reference,
        })
        qr_image = response.get('qr_image') or response.get('qr')
        qr_data = response.get('qr_data') or response.get('in_store_order_id')
        return {
            'order_id': order.id,
            'external_reference': order.external_reference,
            'amount': order.amount,
            'currency': data.get('currency') or self.currency_id.name or self.company_id.currency_id.name,
            'qr_image': qr_image,
            'qr_data': qr_data,
            'public_key': self._mp_mezztt_credentials().get('public_key'),
        }

    def mp_mezztt_poll_status(self, order_id):
        self.ensure_one()
        order = self.env['pos.mercadopago.mezztt.order'].sudo().browse(order_id)
        if not order:
            raise UserError(_('The Mercado Pago order could not be found.'))
        creds, client = self._mp_mezztt_client()
        result = client.get_order_status(order.external_reference)
        status_info = MercadoPagoMezzttClient.extract_payment_status(result)
        status = status_info['status']
        update_vals = {
            'mercado_pago_response': json.dumps(result),
            'status': 'approved' if status == 'approved' else ('rejected' if status == 'rejected' else 'pending'),
            'mercado_pago_payment_id': status_info.get('payment_id'),
        }
        order.write(update_vals)
        return {
            'status': update_vals['status'],
            'payment_id': status_info.get('payment_id'),
            'amount': status_info.get('amount'),
        }

    def mp_mezztt_cancel(self, order_id):
        self.ensure_one()
        if not order_id:
            return True
        order = self.env['pos.mercadopago.mezztt.order'].sudo().browse(order_id)
        if not order:
            return True
        creds, client = self._mp_mezztt_client()
        try:
            client.cancel_qr(creds['collector_id'], creds['pos_id'], creds['terminal_id'])
            order.write({'status': 'cancelled'})
        except Exception as exc:
            _logger.exception('Error cancelling Mercado Pago QR: %s', exc)
        return True

    @api.model
    def mp_mezztt_handle_webhook(self, payload, signature=None):
        if mp_config.WEBHOOK_SECRET and signature != mp_config.WEBHOOK_SECRET:
            _logger.warning('Mercado Pago webhook rejected due to invalid signature.')
            return {'status': 'forbidden'}
        _logger.info('Mercado Pago webhook payload received: %s', payload)
        external_reference = payload.get('data', {}).get('id') or payload.get('resource')
        if not external_reference:
            return {'status': 'ignored'}
        orders = self.env['pos.mercadopago.mezztt.order'].sudo().search([
            ('external_reference', '=', external_reference)
        ])
        if not orders:
            return {'status': 'ignored'}
        orders.write({'status': 'approved'})
        return {'status': 'ok'}
