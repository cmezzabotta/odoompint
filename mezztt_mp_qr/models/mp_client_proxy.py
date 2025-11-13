# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class MercadoPagoClientProxy(models.AbstractModel):
    """Helper abstract model that centralises Mercado Pago client creation."""

    _name = "mezztt_mp_qr.mercadopago_client"
    _description = "Proxy helper to interact with Mercado Pago APIs"

    def _get_service(self):
        return self.env['ir.config_parameter'].sudo()

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------
    def _get_payment_method(self):
        payment_method_id = self.env.context.get('payment_method_id')
        if not payment_method_id:
            return None
        payment_method = self.env['pos.payment.method'].browse(payment_method_id)
        return payment_method if payment_method.exists() else None

    def _settings_credentials(self):
        params = self._get_service()
        return {
            'access_token': params.get_param('mezztt_mp_qr.mp_access_token'),
            'public_key': params.get_param('mezztt_mp_qr.mp_public_key'),
            'user_id': params.get_param('mezztt_mp_qr.mp_user_id'),
            'collector_id': params.get_param('mezztt_mp_qr.mp_collector_id'),
            'integrator_id': params.get_param('mezztt_mp_qr.mp_integrator_id'),
            'sponsor_id': params.get_param('mezztt_mp_qr.mp_sponsor_id'),
            'external_store_id': params.get_param('mezztt_mp_qr.mp_external_store_id'),
            'external_pos_id': params.get_param('mezztt_mp_qr.mp_external_pos_id'),
            'pos_id': params.get_param('mezztt_mp_qr.mp_pos_id'),
            'qr_mode': params.get_param('mezztt_mp_qr.mp_qr_mode') or 'dynamic',
            'notification_url': params.get_param('mezztt_mp_qr.mp_notification_url'),
        }

    def _prepare_client(self, payment_method=None):
        from ..services.mp_client import MercadoPagoClient

        payment_method = payment_method or self._get_payment_method()
        credentials = self._settings_credentials()
        if payment_method:
            credentials = payment_method._mp_credentials(defaults=credentials)
        access_token = credentials.get('access_token')
        if not access_token:
            raise UserError(
                "Debe configurar el Access Token de Mercado Pago en Ajustes > Punto de Venta o en el método de pago."
            )
        return MercadoPagoClient(**credentials)

    # ------------------------------------------------------------------
    # Public helpers used by POS/backends
    # ------------------------------------------------------------------
    def test_connection(self):
        payment_method = self._get_payment_method()
        client = self._prepare_client(payment_method)
        return client.test_connection()

    def create_dynamic_qr(self, payload, payment_method=None):
        client = self._prepare_client(payment_method)
        return client.create_dynamic_qr(payload)

    def check_payment(self, qr_external_reference, payment_method=None):
        client = self._prepare_client(payment_method)
        return client.get_qr_payment(qr_external_reference)

    def update_qr(self, qr_external_reference, payload=None, payment_method=None):
        client = self._prepare_client(payment_method)
        return client.update_qr(qr_external_reference, payload or {})

    def cancel_qr(self, qr_external_reference, payment_method=None):
        client = self._prepare_client(payment_method)
        return client.cancel_qr(qr_external_reference)
