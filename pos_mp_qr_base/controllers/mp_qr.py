# -*- coding: utf-8 -*-
"""Mercado Pago QR controllers for POS."""

import base64
import logging
from datetime import datetime, timedelta

import requests

from odoo import http
from odoo.http import request

try:
    from odoo.tools.misc import generate_qr_code
except Exception:  # pylint: disable=broad-except
    generate_qr_code = None

_logger = logging.getLogger(__name__)


class MercadoPagoQrController(http.Controller):
    """Routes to communicate between the POS frontend and Mercado Pago."""

    def _get_access_token(self):
        token = (
            request.env["ir.config_parameter"].sudo().get_param("pos_mp_qr_base.mercadopago_access_token")
        )
        if not token:
            raise ValueError("No se configuró el token de acceso de Mercado Pago")
        return token

    def _json_response(self, data=None, error=None, status=200):
        if error:
            return request.make_json_response({"error": error}, status=status)
        return request.make_json_response({"result": data or {}})

    @http.route("/mercadopago/qr", type="json", auth="user", methods=["POST"], csrf=False)
    def create_qr(self, **kwargs):
        params = kwargs.get("params") or kwargs
        amount = float(params.get("amount")) if params.get("amount") else 0.0
        description = params.get("description") or "Venta POS"
        external_reference = params.get("external_reference")
        currency = params.get("currency") or request.env.company.currency_id.name
        order_uid = params.get("order_uid")
        pos_session_id = params.get("pos_session_id")

        if not external_reference:
            return self._json_response(error="La referencia externa es obligatoria", status=400)
        if amount <= 0:
            return self._json_response(error="El monto debe ser mayor que cero", status=400)

        try:
            token = self._get_access_token()
        except ValueError as err:
            return self._json_response(error=str(err), status=403)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        preference_payload = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "currency_id": currency,
                    "unit_price": amount,
                }
            ],
            "external_reference": external_reference,
            "notification_url": params.get("notification_url"),
        }

        try:
            response = requests.post(
                "https://api.mercadopago.com/checkout/preferences",
                headers=headers,
                json=preference_payload,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("Error contacting Mercado Pago preference API")
            return self._json_response(error=str(exc), status=502)

        preference = response.json()
        preference_id = preference.get("id")
        init_point = preference.get("init_point") or preference.get("sandbox_init_point")
        qr_base64 = None

        # Some Mercado Pago accounts return QR data under point_of_interaction
        poi = preference.get("point_of_interaction", {})
        txn_data = poi.get("transaction_data") if isinstance(poi, dict) else {}
        if isinstance(txn_data, dict):
            qr_base64 = txn_data.get("qr_code_base64")
            init_point = init_point or txn_data.get("qr_code")

        if not init_point:
            return self._json_response(
                error="Mercado Pago no devolvió un enlace para generar el QR.", status=502
            )

        if not qr_base64 and generate_qr_code:
            try:
                qr_stream = generate_qr_code(init_point)
                qr_base64 = base64.b64encode(qr_stream.getvalue()).decode("ascii")
            except Exception as exc:  # pylint: disable=broad-except
                _logger.warning("No se pudo generar el QR localmente: %s", exc)

        timeout_param = (
            request.env["ir.config_parameter"].sudo().get_param("pos_mp_qr_base.timeout_seconds")
        )
        try:
            timeout_seconds = int(timeout_param)
        except (TypeError, ValueError):
            timeout_seconds = 180

        session_id = None
        if pos_session_id:
            try:
                session_id = int(pos_session_id)
            except (TypeError, ValueError):
                session_id = False
        session_id = session_id or False

        mp_transaction = request.env["pos.mp.qr.transaction"].sudo().create(
            {
                "name": preference_id or external_reference,
                "preference_id": preference_id,
                "external_reference": external_reference,
                "order_uid": order_uid,
                "pos_session_id": session_id,
                "amount": amount,
                "currency_name": currency,
                "status": "pending",
                "qr_init_point": init_point,
                "qr_base64": qr_base64,
                "expiration_at": datetime.utcnow() + timedelta(seconds=timeout_seconds),
            }
        )

        return self._json_response(
            {
                "preference_id": preference_id,
                "init_point": init_point,
                "qr_base64": qr_base64,
                "external_reference": external_reference,
                "transaction_id": mp_transaction.id,
                "timeout_seconds": timeout_seconds,
            }
        )

    @http.route("/mercadopago/status", type="json", auth="user", methods=["POST"], csrf=False)
    def poll_status(self, **kwargs):
        params = kwargs.get("params") or kwargs
        external_reference = params.get("external_reference")
        if not external_reference:
            return self._json_response(error="Referencia externa no informada", status=400)

        try:
            token = self._get_access_token()
        except ValueError as err:
            return self._json_response(error=str(err), status=403)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        query_params = {"external_reference": external_reference, "sort": "date_created", "criteria": "desc"}
        try:
            response = requests.get(
                "https://api.mercadopago.com/v1/payments/search",
                headers=headers,
                params=query_params,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("Error fetching Mercado Pago payment status")
            return self._json_response(error=str(exc), status=502)

        json_response = response.json()
        results = json_response.get("results", [])
        status = "pending"
        payment_id = None
        status_detail = None
        amount = None

        for payment in results:
            payment_id = payment.get("id")
            status = payment.get("status") or status
            status_detail = payment.get("status_detail")
            amount = payment.get("transaction_amount")
            if status == "approved":
                break

        mp_transaction = (
            request.env["pos.mp.qr.transaction"].sudo().search([("external_reference", "=", external_reference)], limit=1)
        )
        if mp_transaction:
            update_vals = {
                "last_status_detail": status_detail,
                "payment_id": payment_id,
            }
            if status == "approved":
                update_vals["status"] = "approved"
            elif status in {"cancelled", "rejected"}:
                update_vals["status"] = "cancelled"
            mp_transaction.write({k: v for k, v in update_vals.items() if v})

        return self._json_response(
            {
                "status": status,
                "status_detail": status_detail,
                "payment_id": payment_id,
                "amount": amount,
            }
        )

    @http.route("/mercadopago/fiscal_qr", type="json", auth="user", methods=["POST"], csrf=False)
    def fiscal_qr(self, **kwargs):
        params = kwargs.get("params") or kwargs
        order_uid = params.get("order_uid")
        pos_reference = params.get("pos_reference")
        domain = []
        if pos_reference:
            domain.append(("pos_reference", "=", pos_reference))
        if order_uid:
            domain.append(("uid", "=", order_uid))
        if not domain:
            return self._json_response(error="Faltan datos para ubicar la orden POS", status=400)
        order = request.env["pos.order"].sudo().search(domain, limit=1, order="id desc")
        if not order:
            return self._json_response(error="Orden POS no encontrada", status=404)
        return self._json_response({"fiscal_qr_url": order._get_fiscal_qr_url()})
