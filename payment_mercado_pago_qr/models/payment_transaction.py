import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    mercado_pago_preference_id = fields.Char(string='Mercado Pago preference')
    mercado_pago_status = fields.Char(string='Mercado Pago status')
    mercado_pago_qr_code_base64 = fields.Text(string='Mercado Pago QR code')
    mercado_pago_init_point = fields.Char(string='Mercado Pago link')

    def _get_specific_rendering_values(self, processing_values):
        self.ensure_one()
        rendering_values = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'mercado_pago_qr':
            return rendering_values

        provider = self.provider_id
        notification_url = provider._mercado_pago_notification_url()
        if not self.mercado_pago_preference_id:
            preference = provider._mercado_pago_create_preference(self, notification_url)
            transaction_data = (preference.get('point_of_interaction') or {}).get('transaction_data') or {}
            qr_image = transaction_data.get('qr_code_base64') or transaction_data.get('qr_code')
            if not qr_image:
                raise ValidationError(_('Mercado Pago did not provide a QR code for this transaction.'))
            self.write({
                'mercado_pago_preference_id': preference.get('id'),
                'mercado_pago_status': 'pending',
                'mercado_pago_qr_code_base64': qr_image,
                'mercado_pago_init_point': preference.get('init_point'),
            })
            rendering_values.update({
                'mercado_pago_qr_image': qr_image,
                'mercado_pago_reference': self.reference,
                'mercado_pago_init_point': preference.get('init_point'),
            })
        else:
            rendering_values.update({
                'mercado_pago_qr_image': self.mercado_pago_qr_code_base64,
                'mercado_pago_reference': self.reference,
                'mercado_pago_init_point': self.mercado_pago_init_point,
            })
        return rendering_values

    @api.model
    def _mercado_pago_qr_handle_notification(self, topic, mp_id, provider):
        _logger.info('Handling Mercado Pago webhook: topic=%s id=%s', topic, mp_id)
        if topic == 'payment':
            payment_data = provider._mercado_pago_make_request('GET', f'/v1/payments/{mp_id}')
            external_reference = payment_data.get('external_reference')
            transaction = self.search([
                ('reference', '=', external_reference),
                ('provider_code', '=', 'mercado_pago_qr'),
            ], limit=1)
            if transaction:
                transaction._mercado_pago_qr_update_state(payment_data)
            else:
                _logger.warning('Mercado Pago webhook payment without matching transaction: %s', mp_id)
        elif topic == 'merchant_order':
            order_data = provider._mercado_pago_make_request('GET', f'/merchant_orders/{mp_id}')
            preference_id = order_data.get('preference_id')
            transaction = self.search([
                ('mercado_pago_preference_id', '=', preference_id),
                ('provider_code', '=', 'mercado_pago_qr'),
            ], limit=1)
            if not transaction:
                _logger.warning('Mercado Pago merchant order without transaction: %s', mp_id)
                return
            payments = order_data.get('payments', [])
            if not payments:
                transaction._mercado_pago_qr_update_state({'status': order_data.get('status')})
                return
            for payment in payments:
                transaction._mercado_pago_qr_update_state(payment)
        else:
            _logger.info('Mercado Pago webhook ignored for topic %s', topic)

    def _mercado_pago_qr_update_state(self, payment_data):
        self.ensure_one()
        status = payment_data.get('status') or payment_data.get('status_detail') or payment_data.get('order_status')
        detail = payment_data.get('status_detail')
        self.write({'mercado_pago_status': status or detail})
        if status == 'approved':
            self._set_done()
        elif status in {'rejected', 'cancelled', 'canceled'}:
            self._set_canceled()
        else:
            if self.state == 'draft':
                self._set_pending()

    def _mercado_pago_qr_poll_status(self):
        for transaction in self.filtered(lambda tx: tx.provider_code == 'mercado_pago_qr' and tx.state in ('draft', 'pending')):
            if not transaction.mercado_pago_preference_id:
                continue
            provider = transaction.provider_id
            response = provider._mercado_pago_make_request(
                'GET',
                '/merchant_orders/search',
                params={'preference_id': transaction.mercado_pago_preference_id},
            )
            elements = response.get('elements', [])
            if not elements:
                continue
            order = elements[0]
            payments = order.get('payments') or []
            if payments:
                transaction._mercado_pago_qr_update_state(payments[0])
            else:
                transaction._mercado_pago_qr_update_state(order)
