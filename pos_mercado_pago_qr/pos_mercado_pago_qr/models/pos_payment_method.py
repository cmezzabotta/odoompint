import json
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from .mercado_pago_qr_client import MercadoPagoQrClient

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    mpqr_use_qr = fields.Boolean(string='Mercado Pago QR', help='Enable Mercado Pago dynamic QR payments in POS.')
    mpqr_access_token = fields.Char(string='Access Token', groups='point_of_sale.group_pos_manager')
    mpqr_collector_id = fields.Char(string='Collector ID', help='Mercado Pago user/collector identifier.', groups='point_of_sale.group_pos_manager')
    mpqr_pos_external_id = fields.Char(string='External POS ID', help='Identifier configured in Mercado Pago for this POS.', groups='point_of_sale.group_pos_manager')
    mpqr_store_id = fields.Char(string='Store ID', groups='point_of_sale.group_pos_manager')
    mpqr_notification_secret = fields.Char(string='Webhook Secret', help='Optional secret to validate Mercado Pago notifications.', groups='point_of_sale.group_pos_manager')
    mpqr_notification_url = fields.Char(string='Webhook URL', compute='_compute_mpqr_notification_url', readonly=True)
    mpqr_order_validity = fields.Integer(string='QR validity (minutes)', default=10, help='Expiration time that will be sent when creating the QR order.')
    mpqr_receipt_message = fields.Text(string='Receipt message', help='Optional message added to Mercado Pago order description.')
    mpqr_integrator_id = fields.Char(string='Integrator ID', help='Identifier provided by Mercado Pago for partners/integrators.', groups='point_of_sale.group_pos_manager')
    mpqr_last_error = fields.Text(string='Last Mercado Pago error', readonly=True)

    def _get_payment_terminal_selection(self):
        selection = list(super()._get_payment_terminal_selection())
        if ('mercado_pago_qr', 'Mercado Pago QR') not in selection:
            selection.append(('mercado_pago_qr', 'Mercado Pago QR'))
        return selection

    @api.depends('mpqr_use_qr')
    def _compute_type(self):
        super()._compute_type()
        for method in self:
            if method.mpqr_use_qr and method.type != 'bank':
                method.type = 'bank'

    @api.depends('company_id')
    def _compute_mpqr_notification_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for method in self:
            method.mpqr_notification_url = f"{base_url}/mercado-pago/pos-qr/webhook" if base_url else False

    @api.constrains('mpqr_use_qr', 'mpqr_access_token', 'mpqr_collector_id', 'mpqr_pos_external_id')
    def _check_mpqr_configuration(self):
        for method in self.filtered('mpqr_use_qr'):
            missing = []
            if not method.mpqr_access_token:
                missing.append(_('Access Token'))
            if not method.mpqr_collector_id:
                missing.append(_('Collector ID'))
            if not method.mpqr_pos_external_id:
                missing.append(_('External POS ID'))
            if missing:
                raise ValidationError(_('The following Mercado Pago QR fields are mandatory: %s') % ', '.join(missing))

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        fields_list += [
            'mpqr_use_qr',
            'mpqr_collector_id',
            'mpqr_pos_external_id',
            'mpqr_store_id',
            'mpqr_order_validity',
            'mpqr_receipt_message',
            'mpqr_integrator_id',
        ]
        return fields_list

    def write(self, vals):
        if self.env.context.get('mpqr_skip_sync'):
            return super().write(vals)

        vals = dict(vals)
        if vals.get('use_payment_terminal') == 'mercado_pago_qr':
            vals.setdefault('mpqr_use_qr', True)

        res = super().write(vals)

        if 'mpqr_use_qr' in vals or vals.get('use_payment_terminal') == 'mercado_pago_qr':
            for method in self:
                if method.mpqr_use_qr:
                    method.with_context(mpqr_skip_sync=True).write({
                        'use_payment_terminal': 'mercado_pago_qr',
                        'payment_method_type': 'terminal',
                    })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        cleaned_vals = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get('use_payment_terminal') == 'mercado_pago_qr':
                vals.setdefault('mpqr_use_qr', True)
            cleaned_vals.append(vals)

        records = super().create(cleaned_vals)
        for method, vals in zip(records, cleaned_vals):
            if vals.get('mpqr_use_qr') or vals.get('use_payment_terminal') == 'mercado_pago_qr':
                method.with_context(mpqr_skip_sync=True).write({
                    'use_payment_terminal': 'mercado_pago_qr',
                    'payment_method_type': 'terminal',
                })
        return records

    # Mercado Pago API helpers -------------------------------------------------

    def _ensure_mpqr_ready(self):
        self.ensure_one()
        if not self.mpqr_use_qr:
            raise UserError(_('This payment method is not configured for Mercado Pago QR payments.'))
        for field_name in ('mpqr_access_token', 'mpqr_collector_id', 'mpqr_pos_external_id'):
            if not getattr(self, field_name):
                raise UserError(_('Field %s is required to create Mercado Pago QR orders.') % field_name)
        return MercadoPagoQrClient(self.sudo().mpqr_access_token)

    def mpqr_prepare_payload(self, order_vals):
        self.ensure_one()
        amount = round(float(order_vals['amount']), 2)
        currency_name = order_vals.get('currency') or self.currency_id.name or self.company_id.currency_id.name
        expires_in = max(int(order_vals.get('expiration_minutes') or self.mpqr_order_validity or 0), 1)
        expiration_date = datetime.utcnow() + timedelta(minutes=expires_in)
        description = order_vals.get('description') or order_vals['reference']
        external_reference = order_vals['external_reference']
        integrator_id = order_vals.get('integrator_id') or self.mpqr_integrator_id

        def _format_amount(value):
            return round(float(value or 0), 2)

        payload = {
            'type': 'qr',
            'total_amount': _format_amount(order_vals.get('total_amount') or amount),
            'description': description,
            'title': order_vals.get('title') or description,
            'external_reference': external_reference,
            'notification_url': self.mpqr_notification_url,
            'expiration_time': f"PT{expires_in}M",
            'expiration_date': expiration_date.strftime('%Y-%m-%dT%H:%M:%S.000-00:00'),
            'currency_id': currency_name,
            'collector_id': self.mpqr_collector_id,
            'pos_id': order_vals.get('external_pos_id') or self.mpqr_pos_external_id,
            'config': {
                'qr': {
                    'external_pos_id': order_vals.get('external_pos_id') or self.mpqr_pos_external_id,
                    'mode': order_vals.get('qr_mode') or 'static',
                }
            },
            'transactions': {
                'payments': [
                    {
                        'amount': _format_amount(order_vals.get('payment_amount') or amount),
                    }
                ]
            },
        }

        if self.mpqr_store_id or order_vals.get('store_id'):
            payload['config']['qr']['store_id'] = order_vals.get('store_id') or self.mpqr_store_id

        if integrator_id:
            payload['integration_data'] = {'integrator_id': integrator_id}

        customer = order_vals.get('customer') or {}
        if customer:
            payload['payer'] = {
                'name': customer.get('name'),
                'email': customer.get('email'),
            }

        sponsor_vat = self.env.company.vat
        if sponsor_vat:
            payload['sponsor'] = {'id': sponsor_vat}

        items = []
        for item in order_vals.get('items') or []:
            title = item.get('title') or description
            unit_price = _format_amount(item.get('unit_price') or amount)
            quantity = int(item.get('quantity') or 1)
            items.append({
                'title': title,
                'description': (item.get('description') or self.mpqr_receipt_message or title)[:250],
                'unit_price': unit_price,
                'quantity': quantity,
                'unit_measure': item.get('unit_measure') or 'unit',
                'total_amount': _format_amount(unit_price * quantity),
                'external_code': item.get('external_code'),
                'external_categories': [
                    {'id': str(category.get('id') if isinstance(category, dict) else category)}
                    for category in (item.get('external_categories') or [])
                    if category
                ],
            })

        if not items:
            items = [
                {
                    'title': description,
                    'description': (self.mpqr_receipt_message or description)[:250],
                    'unit_price': amount,
                    'quantity': 1,
                    'unit_measure': 'unit',
                    'total_amount': amount,
                }
            ]

        payload['items'] = items
        payload['additional_info'] = {
            'print_on_terminal': False,
            'external_reference': external_reference,
            'buyer': {
                'first_name': customer.get('name'),
                'email': customer.get('email'),
            },
        }
        payload['metadata'] = order_vals.get('metadata') or {}
        return payload

    def mpqr_create_order(self, order_vals):
        self.ensure_one()
        payment_method = self.sudo()
        client = payment_method._ensure_mpqr_ready()
        payload = payment_method.mpqr_prepare_payload(order_vals)
        response = client.create_order(payload, payment_method.mpqr_collector_id, payment_method.mpqr_pos_external_id)
        if response.get('error'):
            payment_method.write({'mpqr_last_error': json.dumps(response, ensure_ascii=False)})
            raise UserError(_('Mercado Pago returned an error when creating the QR order: %s') % response.get('error'))
        payment_method.write({'mpqr_last_error': False})
        order = payment_method.env['pos.mercadopago.qr.order'].create_from_payload(payment_method, payload, response)
        return {
            'order_id': order.id,
            'external_reference': order.external_reference,
            'qr_data': response.get('qr_data'),
            'qr_image': response.get('qr_image'),
            'expiration_date': response.get('expiration_date'),
            'amount': order.amount,
            'currency': payment_method.currency_id.name or payment_method.company_id.currency_id.name,
        }

    def mpqr_poll_order(self, order_id):
        self.ensure_one()
        order = self.env['pos.mercadopago.qr.order'].browse(order_id).sudo()
        if not order:
            raise UserError(_('The Mercado Pago QR order could not be found.'))
        if order.payment_method_id != self:
            raise UserError(_('The POS order does not belong to this payment method.'))
        payment_method = order.payment_method_id
        client = payment_method._ensure_mpqr_ready()
        response = client.get_order(
            order.mercadopago_order_id,
            payment_method.mpqr_collector_id,
            payment_method.mpqr_pos_external_id,
        )
        if response.get('error'):
            order.write({'status': 'error', 'last_response': json.dumps(response, ensure_ascii=False)})
            return {'status': 'error', 'detail': response.get('error')}
        order.write_from_response(response)
        status = order.status
        approved_amount = 0
        if status == 'approved':
            payments = response.get('payments') or []
            approved_amount = sum(payment.get('total_paid_amount', 0) for payment in payments if payment.get('status') == 'approved')
        return {
            'status': status,
            'approved_amount': approved_amount,
            'raw': response,
        }

    def mpqr_cancel_order(self, order_id):
        self.ensure_one()
        order = self.env['pos.mercadopago.qr.order'].browse(order_id).sudo()
        if not order:
            return False
        if order.payment_method_id != self:
            return False
        payment_method = order.payment_method_id
        client = payment_method._ensure_mpqr_ready()
        response = client.cancel_order(
            order.mercadopago_order_id,
            payment_method.mpqr_collector_id,
            payment_method.mpqr_pos_external_id,
        )
        order.write({'status': 'cancelled', 'last_response': json.dumps(response, ensure_ascii=False)})
        return True

    @api.model
    def mpqr_prepare_order_payload(self, order_data):
        order_reference = order_data.get('reference') or order_data.get('order_name') or str(uuid4())
        external_reference = f"{order_reference}::{uuid4()}"
        customer = order_data.get('customer') or {}
        currency_name = order_data.get('currency') or self.env.company.currency_id.name
        payload = {
            'reference': order_reference,
            'external_reference': external_reference,
            'amount': float(order_data['amount']),
            'currency': currency_name,
            'customer_name': customer.get('name'),
            'customer_email': customer.get('email'),
            'description': order_data.get('description') or (_('Order %s') % order_reference),
            'title': order_data.get('title') or (_('POS Order %s') % order_reference),
        }
        payload.update({
            'items': order_data.get('items') or [],
            'customer': customer,
            'metadata': order_data.get('metadata') or {},
            'integrator_id': order_data.get('integrator_id'),
            'external_pos_id': order_data.get('external_pos_id'),
            'store_id': order_data.get('store_id'),
            'expiration_minutes': order_data.get('expiration_minutes'),
            'total_amount': order_data.get('total_amount'),
            'payment_amount': order_data.get('payment_amount'),
            'qr_mode': order_data.get('qr_mode'),
        })
        return payload
