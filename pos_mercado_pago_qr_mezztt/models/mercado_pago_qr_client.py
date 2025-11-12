import json
import logging
from typing import Any, Dict

import requests

_logger = logging.getLogger(__name__)


MERCADO_PAGO_API_ENDPOINT = 'https://api.mercadopago.com'
REQUEST_TIMEOUT = 15


class MercadoPagoQrClient:
    """Thin wrapper around Mercado Pago's QR order endpoints."""

    def __init__(self, payment_method):
        """Store the payment method to read credentials from it on each call."""
        self.payment_method = payment_method

    @property
    def access_token(self) -> str:
        return self.payment_method.mpqr_access_token

    @property
    def collector_id(self) -> str:
        return self.payment_method.mpqr_collector_id

    @property
    def external_pos_id(self) -> str:
        return self.payment_method.mpqr_pos_external_id

    def _request(self, method: str, endpoint: str, payload: Dict[str, Any] | None = None, params: Dict[str, Any] | None = None):
        url = f"{MERCADO_PAGO_API_ENDPOINT}{endpoint}"
        headers = {
            'Authorization': f"Bearer {self.access_token}",
            'Content-Type': 'application/json',
            'X-Idempotency-Key': payload.get('external_reference') if payload else None,
        }
        headers = {k: v for k, v in headers.items() if v}
        try:
            response = requests.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                headers=headers,
                data=json.dumps(payload) if payload is not None else None,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            _logger.error("Mercado Pago QR API responded with HTTP error %s: %s", error.response.status_code if error.response else 'n/a', error)
            return {'error': str(error), 'status_code': error.response.status_code if error.response else None, 'content': error.response.json() if error.response else None}
        except requests.exceptions.RequestException as error:
            _logger.exception("Mercado Pago QR API request failed: %s", error)
            return {'error': str(error)}
        except ValueError as error:
            _logger.exception("Unable to decode Mercado Pago QR response: %s", error)
            return {'error': str(error)}

    def _orders_endpoint(self) -> str:
        return f"/instore/qr/seller/collectors/{self.collector_id}/pos/{self.external_pos_id}/orders"

    def create_order(self, payload: Dict[str, Any]):
        endpoint = self._orders_endpoint()
        return self._request('POST', endpoint, payload)

    def get_order(self):
        endpoint = self._orders_endpoint()
        return self._request('GET', endpoint)

    def cancel_order(self):
        endpoint = self._orders_endpoint()
        return self._request('DELETE', endpoint)
