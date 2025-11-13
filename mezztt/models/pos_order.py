# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def action_mezztt_create_qr(self, payload):
        client = self.env['mezztt.mercadopago.client'].sudo()
        order_uid = payload.get('order_uid')
        items = payload.get('items', [])
        amount = payload.get('amount')
        currency = payload.get('currency')
        metadata = {
            'odoo_uid': order_uid,
            'pos_session_id': self.env.context.get('pos_session_id'),
        }
        order_data = {
            'external_reference': order_uid,
            'amount': amount,
            'currency': currency,
            'items': [
                {
                    'title': item.get('name'),
                    'quantity': item.get('quantity'),
                    'unit_price': item.get('unit_price'),
                    'description': item.get('name'),
                }
                for item in items
            ],
            'metadata': metadata,
            'title': 'Orden POS %s' % (order_uid,),
            'description': 'Compra realizada desde Odoo POS',
        }
        _logger.info('Creando QR Mercado Pago para orden POS %s', order_uid)
        response = client.create_dynamic_qr(order_data)
        qr_data = response.get('qr_data') if isinstance(response, dict) else None
        qr_image = None
        if qr_data:
            qr_image = 'data:image/png;base64,%s' % qr_data
        return {
            'qr_data': qr_data,
            'qr_image': qr_image,
            'external_reference': response.get('external_reference') if isinstance(response, dict) else order_uid,
            'message': response.get('message') if isinstance(response, dict) else '',
        }

    @api.model
    def action_mezztt_check_payment(self, external_reference):
        client = self.env['mezztt.mercadopago.client'].sudo()
        return client.check_payment(external_reference)
