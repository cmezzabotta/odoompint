import json
import logging
from typing import Any, Dict

import requests

_logger = logging.getLogger(__name__)

MERCADO_PAGO_API_ENDPOINT = "https://api.mercadopago.com"


class MercadoPagoMezzttClient:
    """Very small HTTP client for the Mercado Pago REST API."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    # QR management ---------------------------------------------------------

    def create_qr(self, collector_id: str, pos_id: str, terminal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = (
            f"{MERCADO_PAGO_API_ENDPOINT}/instore/orders/qr/seller/collectors/{collector_id}/"
            f"pos/{pos_id}/qrs/{terminal_id}"
        )
        _logger.info("[MP][QR] Creating QR order -> %s", url)
        response = self.session.post(url, data=json.dumps(payload))
        return self._handle_response(response)

    def get_order_status(self, external_reference: str) -> Dict[str, Any]:
        params = {
            "external_reference": external_reference,
            "sort": "date_created",
            "criteria": "desc",
        }
        url = f"{MERCADO_PAGO_API_ENDPOINT}/v1/payments/search"
        _logger.debug("[MP][QR] Searching payment -> %s params=%s", url, params)
        response = self.session.get(url, params=params)
        return self._handle_response(response)

    def cancel_qr(self, collector_id: str, pos_id: str, terminal_id: str) -> Dict[str, Any]:
        url = (
            f"{MERCADO_PAGO_API_ENDPOINT}/instore/orders/qr/seller/collectors/{collector_id}/"
            f"pos/{pos_id}/qrs/{terminal_id}"
        )
        _logger.info("[MP][QR] Cancelling QR order -> %s", url)
        response = self.session.delete(url)
        return self._handle_response(response)

    # Helpers ---------------------------------------------------------------

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not response.ok:
            _logger.error("[MP] API error %s -> %s", response.status_code, payload)
            response.raise_for_status()
        _logger.debug("[MP] API response -> %s", payload)
        return payload

    @staticmethod
    def extract_payment_status(search_result: Dict[str, Any]) -> Dict[str, Any]:
        results = (search_result or {}).get("results") or []
        if not results:
            return {"status": "pending"}
        payment = results[0]
        status = payment.get("status") or "pending"
        total_paid = payment.get("transaction_amount", 0)
        return {
            "status": status,
            "payment_id": payment.get("id"),
            "amount": total_paid,
            "raw": payment,
        }
