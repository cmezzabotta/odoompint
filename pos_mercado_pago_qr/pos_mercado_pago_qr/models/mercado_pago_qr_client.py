import json
import logging
from typing import Any, Dict

import requests

_logger = logging.getLogger(__name__)


MERCADO_PAGO_API_ENDPOINT = 'https://api.mercadopago.com'
REQUEST_TIMEOUT = 15


class MercadoPagoQrClient:
    """Thin wrapper around Mercado Pago's QR order endpoints."""

    def __init__(self, access_token: str):
        self.access_token = access_token

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

    def create_order(self, payload: Dict[str, Any], collector_id: str | None = None, external_pos_id: str | None = None):
        if collector_id and external_pos_id:
            endpoint = f"/instore/qr/seller/collectors/{collector_id}/pos/{external_pos_id}/orders"
        else:
            endpoint = "/v1/orders"
        return self._request('POST', endpoint, payload)

    def get_order(
        self,
        order_id: str | None = None,
        collector_id: str | None = None,
        external_pos_id: str | None = None,
    ):
        if order_id:
            endpoint = f"/v1/orders/{order_id}"
        elif collector_id and external_pos_id:
            endpoint = f"/instore/qr/seller/collectors/{collector_id}/pos/{external_pos_id}/orders"
        else:
            raise ValueError("An order identifier or collector/POS identifiers must be provided to poll Mercado Pago.")
        return self._request('GET', endpoint)

    def cancel_order(
        self,
        order_id: str | None = None,
        collector_id: str | None = None,
        external_pos_id: str | None = None,
    ):
        if order_id:
            endpoint = f"/v1/orders/{order_id}"
            return self._request('DELETE', endpoint)
        if collector_id and external_pos_id:
            endpoint = f"/instore/qr/seller/collectors/{collector_id}/pos/{external_pos_id}/orders"
            return self._request('DELETE', endpoint)
        raise ValueError("An order identifier or collector/POS identifiers must be provided to cancel Mercado Pago orders.")
