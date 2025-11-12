import json
import logging
from typing import Any, Dict, Optional

import requests

from odoo import http
from odoo.http import request

from ..models.res_config_settings import (
    PARAM_ACCESS_TOKEN,
    PARAM_PUBLIC_KEY,
    PARAM_SANDBOX,
)

_logger = logging.getLogger(__name__)

FINAL_STATES = {"approved", "rejected", "cancelled"}
DEFAULT_TIMEOUT = 20


def _mp_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _base_url(use_sandbox: bool) -> str:
    # TODO: Confirm sandbox host for QR dinámico una vez que se cuenten con credenciales reales.
    return "https://api.mercadopago.com"


class MpMezzttController(http.Controller):
    @staticmethod
    def _get_credentials() -> Dict[str, Any]:
        icp = request.env["ir.config_parameter"].sudo()
        return {
            "token": icp.get_param(PARAM_ACCESS_TOKEN, default=""),
            "public_key": icp.get_param(PARAM_PUBLIC_KEY, default=""),
            "sandbox": icp.get_param(PARAM_SANDBOX, default="0") == "1",
        }

    @http.route("/mp/mezztt/create", type="json", auth="user", methods=["POST"])
    def mp_create(self, **_payload):
        creds = self._get_credentials()
        token = creds["token"]
        if not token:
            return {"error": "Faltan credenciales de Mercado Pago (Access Token)."}

        data = request.jsonrequest or {}
        amount = data.get("amount")
        currency_code = data.get("currency")
        order_ref = data.get("order_ref")
        pos_session_id = data.get("pos_session_id")

        try:
            amount_value = float(amount)
        except (TypeError, ValueError):
            return {"error": "El monto proporcionado no es válido."}

        if amount_value <= 0 or not order_ref:
            return {"error": "Datos incompletos para crear el QR."}

        pos_session = None
        if pos_session_id:
            try:
                pos_session = request.env["pos.session"].sudo().browse(int(pos_session_id))
            except (TypeError, ValueError):
                return {"error": "La sesión de POS indicada no es válida."}
            if not pos_session.exists():
                return {"error": "La sesión de POS indicada no existe."}

        currency = None
        if currency_code:
            currency = request.env["res.currency"].sudo().search([("name", "=", currency_code)], limit=1)

        # TODO: completar endpoint y payload con collector_id, pos_id y demás datos requeridos por MP.
        mp_url = f"{_base_url(creds['sandbox'])}/instore/orders/qr/seller/collectors/{{collector_id}}/pos/{{pos_id}}/qrs"
        notification_url = f"{request.httprequest.host_url.rstrip('/')}/mp/mezztt/webhook"

        body = {
            "title": f"POS Order {order_ref}",
            "description": "Pago QR POS",
            "external_reference": order_ref,
            "total_amount": amount_value,
            "items": [
                {
                    "title": "POS",
                    "unit_price": amount_value,
                    "quantity": 1,
                    "currency_id": currency_code or (currency.name if currency else "ARS"),
                }
            ],
            "notification_url": notification_url,
            # TODO: agregar metadata requerida por MP (p.e. sponsor_id, store_id, etc.).
        }

        try:
            response = requests.post(
                mp_url,
                headers=_mp_headers(token),
                data=json.dumps(body),
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            mp_payload = response.json() if response.content else {}
        except requests.RequestException as err:
            _logger.exception("Error al crear pago en Mercado Pago")
            return {"error": str(err)}

        payment_id = mp_payload.get("id") or mp_payload.get("qr_data_id")
        if not payment_id:
            # TODO: validar el campo exacto devuelto por la API de QR dinámico.
            _logger.warning("Mercado Pago no devolvió un payment_id identificable: %s", mp_payload)
            return {"error": "No se pudo obtener el identificador de pago."}

        payment_vals = {
            "payment_id": payment_id,
            "external_reference": mp_payload.get("external_reference", order_ref),
            "pos_session_id": pos_session.id if pos_session else False,
            "amount": amount_value,
            "currency_id": currency.id if currency else False,
            "status": mp_payload.get("status", "pending"),
            "details": json.dumps(mp_payload, ensure_ascii=False) if mp_payload else False,
        }
        request.env["pos.mercado_pago.mezztt.payment"].upsert_payment(payment_vals)

        return {
            "payment_id": payment_id,
            "external_reference": payment_vals["external_reference"],
            "qr_base64": mp_payload.get("qr", mp_payload.get("qr_data")),
            "qr_url": mp_payload.get("qr_image"),
        }

    @http.route("/mp/mezztt/status/<string:payment_id>", type="json", auth="user", methods=["GET"])
    def mp_status(self, payment_id: str, **_kwargs):
        creds = self._get_credentials()
        token = creds["token"]
        if not token:
            return {"error": "Faltan credenciales de Mercado Pago."}

        payment_model = request.env["pos.mercado_pago.mezztt.payment"]
        payment = payment_model.sudo().search([("payment_id", "=", payment_id)], limit=1)
        cached_status = payment.status if payment else None

        should_query_mp = not cached_status or cached_status not in FINAL_STATES
        mp_payload: Optional[Dict[str, Any]] = None
        if should_query_mp:
            mp_url = f"{_base_url(creds['sandbox'])}/v1/payments/{payment_id}"
            try:
                response = requests.get(mp_url, headers=_mp_headers(token), timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                mp_payload = response.json() if response.content else {}
            except requests.RequestException as err:
                _logger.exception("Error consultando estado en Mercado Pago")
                return {"error": str(err)}

            if payment:
                payment.update_from_mp_response(mp_payload)
            else:
                payment_vals = {
                    "payment_id": payment_id,
                    "status": mp_payload.get("status", "pending"),
                    "details": json.dumps(mp_payload, ensure_ascii=False) if mp_payload else False,
                }
                if mp_payload and mp_payload.get("external_reference"):
                    payment_vals["external_reference"] = mp_payload.get("external_reference")
                payment = payment_model.upsert_payment(payment_vals)

        result_payload: Dict[str, Any] = mp_payload or {}
        if not result_payload and payment and payment.details:
            try:
                result_payload = json.loads(payment.details)
            except json.JSONDecodeError:
                result_payload = {}
        status = payment.status if payment else result_payload.get("status", "pending")
        metadata = {
            "external_reference": payment.external_reference if payment else result_payload.get("external_reference"),
            "authorization_code": result_payload.get("authorization_code"),
            "mp_raw": result_payload,
        }

        return {
            "status": status,
            "payment_id": payment_id,
            "metadata": metadata,
        }

    @http.route("/mp/mezztt/webhook", type="http", auth="public", methods=["POST"], csrf=False)
    def mp_webhook(self, **_kwargs):
        # TODO: validar firma de Mercado Pago (header X-Hub-Signature u otro mecanismo según configuración).
        raw_body = request.httprequest.data or b""
        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            _logger.warning("Webhook de Mercado Pago con payload no JSON: %s", raw_body)
            payload = {}

        payment_id = payload.get("data", {}).get("id") or payload.get("id")
        if not payment_id:
            _logger.info("Webhook Mercado Pago sin payment_id: %s", payload)
            return request.make_response("ok")

        payment_model = request.env["pos.mercado_pago.mezztt.payment"]
        payment = payment_model.sudo().search([("payment_id", "=", payment_id)], limit=1)
        if payment:
            payment.update_from_mp_response(payload)
        else:
            payment_model.upsert_payment({
                "payment_id": payment_id,
                "status": payload.get("status", "pending"),
                "details": json.dumps(payload, ensure_ascii=False) if payload else False,
            })

        return request.make_response("ok")
