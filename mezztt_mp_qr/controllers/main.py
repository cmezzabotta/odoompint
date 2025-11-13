# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoController(http.Controller):
    """JSON endpoints used to administrar el flujo de Mercado Pago desde Odoo.

    Aunque el POS utiliza RPC directo contra ``pos.order``, dejamos expuesto un
    pequeño controlador para cubrir los casos en los que se necesite operar
    contra la API desde otras vistas (por ejemplo, para pruebas manuales o
    integraciones adicionales).
    """

    def _client(self, payment_method_id=None):
        client = request.env['mezztt_mp_qr.mercadopago_client'].sudo()
        if payment_method_id:
            return client.with_context(payment_method_id=payment_method_id)
        return client

    @http.route('/mezztt_mp_qr/api/qr', type='json', auth='user', methods=['POST'])
    def create_qr(self, **payload):
        payment_method_id = payload.get('payment_method_id')
        order_data = payload.get('order') or {}
        _logger.info(
            "Generando QR dinámico Mercado Pago (controller) para referencia %s",
            order_data.get('external_reference') or order_data.get('order_uid'),
        )
        return self._client(payment_method_id).create_dynamic_qr(order_data)

    @http.route(
        '/mezztt_mp_qr/api/qr/<string:external_reference>',
        type='json',
        auth='user',
        methods=['GET'],
    )
    def check_qr(self, external_reference, payment_method_id=None):
        _logger.debug("Consultando estado del QR %s desde controlador", external_reference)
        return self._client(payment_method_id).check_payment(external_reference)

    @http.route(
        '/mezztt_mp_qr/api/qr/<string:external_reference>',
        type='json',
        auth='user',
        methods=['PUT'],
    )
    def update_qr(self, external_reference, **payload):
        payment_method_id = payload.get('payment_method_id')
        body = payload.get('body') or {}
        _logger.info("Actualizando QR %s desde controlador", external_reference)
        return self._client(payment_method_id).update_qr(external_reference, body)

    @http.route(
        '/mezztt_mp_qr/api/qr/<string:external_reference>',
        type='json',
        auth='user',
        methods=['DELETE'],
    )
    def cancel_qr(self, external_reference, payment_method_id=None):
        _logger.info("Cancelando QR dinámico %s desde controlador", external_reference)
        return self._client(payment_method_id).cancel_qr(external_reference)
