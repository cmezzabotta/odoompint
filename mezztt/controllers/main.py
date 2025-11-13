# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoController(http.Controller):
    @http.route('/mezztt/mercadopago/qr', type='json', auth='user', methods=['POST'])
    def create_qr(self, **payload):
        client = request.env['mezztt.mercadopago.client'].sudo()
        order_data = payload.get('order') or {}
        _logger.info("Generando QR dinámico para la orden POS: %s", order_data.get('external_reference'))
        response = client.create_dynamic_qr(order_data)
        return response

    @http.route('/mezztt/mercadopago/qr/<string:external_reference>', type='json', auth='user', methods=['GET'])
    def check_qr(self, external_reference):
        client = request.env['mezztt.mercadopago.client'].sudo()
        _logger.debug("Consultando estado del QR %s", external_reference)
        return client.check_payment(external_reference)

    @http.route('/mezztt/mercadopago/qr/<string:external_reference>', type='json', auth='user', methods=['DELETE'])
    def cancel_qr(self, external_reference):
        client = request.env['mezztt.mercadopago.client'].sudo()
        _logger.info("Cancelando QR dinámico %s", external_reference)
        return client.cancel_qr(external_reference)
