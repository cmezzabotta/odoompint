import logging
from typing import Any, Dict, Optional

import requests

from odoo import _, models
from odoo.exceptions import UserError

from . import mp_config

_logger = logging.getLogger(__name__)


class MercadoPagoQRService(models.AbstractModel):
    """Pequeño cliente Mercado Pago reutilizable desde controladores."""

    _name = "pos.mercado_pago_mezztt.service"
    _description = "Servicio Mercado Pago QR para POS (_mezztt)"

    MP_API_BASE = "https://api.mercadopago.com"

    # ------------------------------------------------------------------
    # Credenciales y utilidades
    # ------------------------------------------------------------------
    def _get_provider_from_payment_method(self, payment_method_id: int):
        Provider = self.env["payment.provider"].sudo()
        if payment_method_id:
            payment_method = self.env["pos.payment.method"].sudo().browse(payment_method_id)
            if payment_method and payment_method.payment_provider_id:
                return payment_method.payment_provider_id
        provider = Provider.search([("code", "=", "mercado_pago")], limit=1)
        if not provider:
            provider = Provider.search([("name", "ilike", "Mercado Pago")], limit=1)
        return provider

    def _get_credentials(self, payment_method_id: int) -> Dict[str, Any]:
        provider = self._get_provider_from_payment_method(payment_method_id)

        access_token = False
        public_key = False
        if provider:
            access_token = getattr(provider, "mercado_pago_access_token", False) or getattr(
                provider, "access_token", False
            )
            public_key = getattr(provider, "mercado_pago_public_key", False) or getattr(
                provider, "public_key", False
            )

        access_token = access_token or mp_config.MP_ACCESS_TOKEN
        public_key = public_key or mp_config.MP_PUBLIC_KEY

        if not access_token:
            raise UserError(
                _(
                    "No se encontró un Access Token válido para Mercado Pago. "
                    "Configura el proveedor 'Mercado Pago (Pago Online)' o completa"
                    " el archivo mp_config.py."
                )
            )

        collector_id = mp_config.COLLECTOR_ID
        pos_id = mp_config.POS_ID
        external_pos_id = mp_config.EXTERNAL_POS_ID or pos_id
        terminal_id = mp_config.TERMINAL_ID

        missing_terminal_values = [value for value in (collector_id, pos_id, external_pos_id) if not value]
        if missing_terminal_values:
            raise UserError(
                _(
                    "Faltan credenciales de la caja en mp_config.py. "
                    "Asegúrate de completar COLLECTOR_ID, POS_ID y EXTERNAL_POS_ID."
                )
            )

        return {
            "access_token": access_token,
            "public_key": public_key,
            "collector_id": collector_id,
            "pos_id": pos_id,
            "external_pos_id": external_pos_id,
            "terminal_id": terminal_id,
        }

    def _build_headers(self, access_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _get_notification_url(self) -> str:
        if mp_config.NOTIFICATION_URL:
            return mp_config.NOTIFICATION_URL
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        if not base_url:
            _logger.warning(
                "No se pudo determinar web.base.url, usando dominio local para webhook."
            )
        return f"{base_url.rstrip('/')}/mp/mezztt/webhook"

    # ------------------------------------------------------------------
    # Llamadas a la API de Mercado Pago
    # ------------------------------------------------------------------
    def _do_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.MP_API_BASE}{endpoint}"
        headers = self._build_headers(access_token)
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=payload,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("Error comunicando con Mercado Pago: %s", exc)
            raise UserError(_("No se pudo contactar con la API de Mercado Pago. Ver logs.")) from exc
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - dependemos del API externo
            _logger.exception("Respuesta inesperada de Mercado Pago: %s", exc)
            raise UserError(_("Respuesta no válida desde Mercado Pago.")) from exc

    def create_qr_order(
        self,
        amount: float,
        currency: str,
        order_reference: str,
        payment_method_id: int,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        creds = self._get_credentials(payment_method_id)
        endpoint = \
            f"/instore/orders/qr/{creds['collector_id']}/{creds['pos_id']}/{creds['external_pos_id']}"
        payload = {
            "external_reference": order_reference,
            "title": description or order_reference,
            "description": description or order_reference,
            "total_amount": round(amount, 2),
            "currency_id": currency,
            "notification_url": self._get_notification_url(),
            "sponsor": {"id": creds["collector_id"]},
            "items": [
                {
                    "title": description or order_reference,
                    "quantity": 1,
                    "unit_price": round(amount, 2),
                    "currency_id": currency,
                }
            ],
        }
        _logger.info("Creando orden QR Mercado Pago para %s por %s %s", order_reference, amount, currency)
        data = self._do_request("POST", endpoint, creds["access_token"], payload=payload)
        qr_data = data.get("qr_data") or data.get("data", {}).get("qr_data")
        qr_image = data.get("qr_image") or data.get("data", {}).get("qr_image")
        in_store_order_id = data.get("in_store_order_id") or data.get("id")

        return {
            "qr_data": qr_data,
            "qr_image": qr_image,
            "in_store_order_id": in_store_order_id,
            "external_reference": order_reference,
            "public_key": creds["public_key"],
            "terminal_id": creds["terminal_id"],
        }

    def get_payment_status(self, external_reference: str, payment_method_id: int) -> Dict[str, Any]:
        creds = self._get_credentials(payment_method_id)
        params = {
            "external_reference": external_reference,
            "sort": "date_created",
            "criteria": "desc",
        }
        _logger.debug("Consultando estado de pago Mercado Pago %s", external_reference)
        data = self._do_request("GET", "/v1/payments/search", creds["access_token"], params=params)
        results = data.get("results", [])
        if not results:
            return {
                "status": "pending",
                "external_reference": external_reference,
            }
        payment = results[0]
        return {
            "status": payment.get("status", "pending"),
            "status_detail": payment.get("status_detail"),
            "payment_id": payment.get("id"),
            "external_reference": external_reference,
        }

    def get_payment_details(self, payment_id: str, payment_method_id: int) -> Dict[str, Any]:
        creds = self._get_credentials(payment_method_id)
        endpoint = f"/v1/payments/{payment_id}"
        _logger.debug("Consultando pago Mercado Pago ID %s", payment_id)
        return self._do_request("GET", endpoint, creds["access_token"])

