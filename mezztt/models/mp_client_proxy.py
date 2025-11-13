# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class MercadoPagoClientProxy(models.AbstractModel):
    _name = "mezztt.mercadopago.client"
    _description = "Proxy helper to interact with Mercado Pago APIs"

    def _get_service(self):
        return self.env['ir.config_parameter'].sudo()

    def _prepare_client(self):
        from ..services.mp_client import MercadoPagoClient

        params = self.env['ir.config_parameter'].sudo()
        access_token = params.get_param('mezztt.mp_access_token')
        if not access_token:
            raise UserError("Debe configurar el Access Token de Mercado Pago en Ajustes > Punto de Venta.")
        return MercadoPagoClient(
            access_token=access_token,
            public_key=params.get_param('mezztt.mp_public_key'),
            user_id=params.get_param('mezztt.mp_user_id'),
            collector_id=params.get_param('mezztt.mp_collector_id'),
            integrator_id=params.get_param('mezztt.mp_integrator_id'),
            sponsor_id=params.get_param('mezztt.mp_sponsor_id'),
            external_store_id=params.get_param('mezztt.mp_external_store_id'),
            external_pos_id=params.get_param('mezztt.mp_external_pos_id'),
            pos_id=params.get_param('mezztt.mp_pos_id'),
            qr_mode=params.get_param('mezztt.mp_qr_mode') or 'dynamic',
            notification_url=params.get_param('mezztt.mp_notification_url'),
        )

    def test_connection(self):
        client = self._prepare_client()
        return client.test_connection()

    def create_dynamic_qr(self, payload):
        client = self._prepare_client()
        return client.create_dynamic_qr(payload)

    def check_payment(self, qr_external_reference):
        client = self._prepare_client()
        return client.get_qr_payment(qr_external_reference)

    def cancel_qr(self, qr_external_reference):
        client = self._prepare_client()
        return client.cancel_qr(qr_external_reference)
