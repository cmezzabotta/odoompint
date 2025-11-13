# -*- coding: utf-8 -*-
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

_logger = logging.getLogger(__name__)


@dataclass
class MercadoPagoClient:
    """Ligero cliente HTTP para la API de QR dinámico de Mercado Pago."""

    access_token: str
    public_key: Optional[str] = None
    user_id: Optional[str] = None
    collector_id: Optional[str] = None
    integrator_id: Optional[str] = None
    sponsor_id: Optional[str] = None
    external_store_id: Optional[str] = None
    external_pos_id: Optional[str] = None
    pos_id: Optional[str] = None
    qr_mode: str = "dynamic"
    notification_url: Optional[str] = None

    api_url: str = "https://api.mercadopago.com"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if self.integrator_id:
            headers["X-Integrator-Id"] = self.integrator_id
        if self.sponsor_id:
            headers["X-Idempotency-Key"] = self.sponsor_id
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ):
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        _logger.debug("Mercado Pago %s %s payload=%s", method, url, payload)
        response = requests.request(method, url, headers=self._headers(), json=payload, timeout=30)
        if response.status_code >= 400:
            _logger.error("Mercado Pago error %s: %s", response.status_code, response.text)
            raise ValueError(f"Mercado Pago error {response.status_code}: {response.text}")
        if response.text:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        return {}

    # -- Public helpers -----------------------------------------------------
    def test_connection(self) -> str:
        result = self._request("GET", "/users/me")
        return str(result.get("id") or result)

    def create_dynamic_qr(self, payload: Dict[str, Any]):
        if not self.external_store_id or not self.external_pos_id:
            raise ValueError(
                "Es necesario configurar External Store ID y External POS ID para generar un QR."
            )
        body = {
            "external_store_id": self.external_store_id,
            "external_pos_id": self.external_pos_id,
            "notification_url": self.notification_url,
            "cash_out": {"enable": False},
            "metadata": payload.get("metadata") or {},
            "title": payload.get("title") or "Orden POS",
            "description": payload.get("description") or "Orden generada desde Odoo POS",
            "amount": payload.get("amount"),
            "items": payload.get("items"),
        }
        if self.qr_mode == "static":
            body.pop("amount", None)
        return self._request(
            "POST",
            "/instore/orders/qr/seller/collectors/%s/pos/%s/qrs"
            % (self.collector_id or self.user_id, self.pos_id or self.external_pos_id),
            body,
        )

    def get_qr_payment(self, external_reference: str):
        endpoint = "/instore/orders/qr/seller/collectors/%s/pos/%s/orders/%s" % (
            self.collector_id or self.user_id,
            self.pos_id or self.external_pos_id,
            external_reference,
        )
        return self._request("GET", endpoint)

    def update_qr(self, external_reference: str, payload: Dict[str, Any]):
        endpoint = "/instore/orders/qr/seller/collectors/%s/pos/%s/orders/%s" % (
            self.collector_id or self.user_id,
            self.pos_id or self.external_pos_id,
            external_reference,
        )
        return self._request("PUT", endpoint, payload)

    def cancel_qr(self, external_reference: str):
        endpoint = "/instore/orders/qr/seller/collectors/%s/pos/%s/orders/%s" % (
            self.collector_id or self.user_id,
            self.pos_id or self.external_pos_id,
            external_reference,
        )
        return self._request("DELETE", endpoint)
