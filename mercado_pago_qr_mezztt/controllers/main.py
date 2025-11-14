# -*- coding: utf-8 -*-
"""HTTP controllers that proxy Mercado Pago API calls for the POS frontend.

The POS nunca se conecta directo a Mercado Pago; siempre pasa por estos
endpoints para mantener las credenciales en el servidor y poder registrar el
estado localmente.  Cada controlador está intensamente documentado para que el
futuro mantenimiento sea sencillo.
"""

import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import http
from odoo.http import request

from ..mp_config import MP_CONFIG

_logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.mercadopago.com/v1"


def _build_headers():
    """Return the HTTP headers required by Mercado Pago."""

    headers = {
        "Authorization": f"Bearer {MP_CONFIG['ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }
    # Mercado Pago recomienda enviar un idempotency key para evitar órdenes
    # duplicadas cuando hay reintentos.  Utilizamos la marca temporal.
    headers["X-Idempotency-Key"] = datetime.utcnow().isoformat()
    if MP_CONFIG.get("PLATFORM_ID"):
        headers["X-Platform-Id"] = MP_CONFIG["PLATFORM_ID"]
    if MP_CONFIG.get("INTEGRATOR_ID"):
        headers["X-Integrator-Id"] = MP_CONFIG["INTEGRATOR_ID"]
    return headers


def _mp_timeout():
    """Timeout razonable para las llamadas HTTP (segundos)."""

    return 15


class MercadoPagoQrController(http.Controller):
    """Expose POS-friendly endpoints for Mercado Pago QR static integration."""

    @http.route(
        "/mercado_pago_qr_mezztt/create_order",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def create_order(self, **payload):
        """Create an in-store order in Mercado Pago.

        Expected payload (simplified)::

            {
                "pos_reference": "SESSION123",
                "total_amount": 740.0,
                "currency": "ARS",
                "items": [
                    {"name": "Producto", "quantity": 1, "unit_price": 499.0}
                ]
            }

        Returns the Mercado Pago order id (``id``).
        """

        _logger.info("Creating Mercado Pago order for POS ref %s", payload.get("pos_reference"))
        if not MP_CONFIG.get("ACCESS_TOKEN") or "XXX" in MP_CONFIG["ACCESS_TOKEN"]:
            return {"error": "ACCESS_TOKEN not configured. Edit mp_config.py."}

        pos_reference = payload.get("pos_reference") or "pos-unknown"
        total_amount = payload.get("total_amount")
        currency = payload.get("currency", "ARS")
        items = payload.get("items", [])
        if not total_amount:
            return {"error": "total_amount is required"}

        # Mercado Pago espera strings para montos con 2 decimales.
        amount_str = f"{float(total_amount):.2f}"
        expiration = datetime.utcnow() + timedelta(minutes=16)

        body = {
            "type": "qr",
            "total_amount": amount_str,
            "description": f"POS {pos_reference}",
            "external_reference": pos_reference,
            "expiration_time": "PT16M",
            "config": {
                "qr": {
                    "external_pos_id": MP_CONFIG["POS_ID"],
                    "mode": "static",
                }
            },
            "transactions": {"payments": [{"amount": amount_str}]},
            "items": [
                {
                    "title": line.get("name", "Producto"),
                    "quantity": line.get("quantity", 1),
                    "unit_price": f"{float(line.get('unit_price', 0.0)):.2f}",
                    "unit_measure": line.get("unit_measure", "unit"),
                    "external_code": line.get("external_code", "odoo-pos"),
                }
                for line in items
            ],
            "integration_data": {},
            "collector_id": MP_CONFIG["COLLECTOR_ID"],
        }
        if MP_CONFIG.get("BRANCH_ID"):
            body["branch_id"] = MP_CONFIG["BRANCH_ID"]
        if MP_CONFIG.get("SPONSOR_ID"):
            body.setdefault("integration_data", {})["sponsor"] = {"id": MP_CONFIG["SPONSOR_ID"]}
        if MP_CONFIG.get("INTEGRATOR_ID"):
            body.setdefault("integration_data", {})["integrator_id"] = MP_CONFIG["INTEGRATOR_ID"]
        if MP_CONFIG.get("PLATFORM_ID"):
            body.setdefault("integration_data", {})["platform_id"] = MP_CONFIG["PLATFORM_ID"]

        try:
            response = requests.post(
                f"{API_BASE_URL}/orders",
                headers=_build_headers(),
                json=body,
                timeout=_mp_timeout(),
            )
            response.raise_for_status()
        except requests.RequestException as err:
            _logger.exception("Mercado Pago order creation failed: %s", err)
            return {"error": str(err)}

        mp_data = response.json()
        order_id = mp_data.get("id")
        if not order_id:
            _logger.error("Unexpected Mercado Pago response: %s", mp_data)
            return {"error": "Missing order id"}

        # Persist minimal tracking information for polling and webhook usage.
        request.env["mercado.pago.qr.order"].sudo().register_order(
            pos_reference=pos_reference,
            mp_order_id=order_id,
            payload=json.dumps(mp_data),
        )

        return {
            "order_id": order_id,
            "status": mp_data.get("status", "pending"),
            "qr_url": MP_CONFIG["STATIC_QR_URL"],
            "expires_at": expiration.isoformat(),
            "currency": currency,
        }

    @http.route(
        "/mercado_pago_qr_mezztt/order_status/<string:order_id>",
        type="json",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def order_status(self, order_id):
        """Return the latest status of the given Mercado Pago order."""

        _logger.debug("Polling status for Mercado Pago order %s", order_id)
        try:
            response = requests.get(
                f"{API_BASE_URL}/orders/{order_id}",
                headers=_build_headers(),
                timeout=_mp_timeout(),
            )
            response.raise_for_status()
        except requests.RequestException as err:
            _logger.exception("Mercado Pago status request failed: %s", err)
            return {"error": str(err)}

        data = response.json()
        status = data.get("status", "pending")
        # Store the fresh status for reference/webhook debugging.
        request.env["mercado.pago.qr.order"].sudo().register_order(
            pos_reference=data.get("external_reference", "unknown"),
            mp_order_id=order_id,
            status=status,
            payload=json.dumps(data),
        )
        return {"status": status, "raw": data}

    @http.route(
        "/mercado_pago_qr_mezztt/webhook",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def webhook(self):
        """Handle asynchronous notifications from Mercado Pago.

        The payload format is documented at
        https://www.mercadopago.com/developers/en/reference.  Recibimos el
        ``order_id`` y su estado.  Siempre respondemos 200 OK para evitar
        reintentos innecesarios.
        """

        data = request.jsonrequest or {}
        _logger.info("Mercado Pago webhook received: %s", data)
        order_id = data.get("data", {}).get("id") or data.get("id")
        status = data.get("type") or data.get("status")
        if order_id:
            request.env["mercado.pago.qr.order"].sudo().register_order(
                pos_reference=data.get("external_reference", "webhook"),
                mp_order_id=order_id,
                status=status or "pending",
                payload=json.dumps(data),
            )
        return {"received": True}
