import json, logging, requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ..models.res_config_settings import PARAM_ACCESS_TOKEN, PARAM_PUBLIC_KEY, PARAM_SANDBOX

def _mp_headers(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

class MpMezzttController(http.Controller):

    @http.route("/mp/mezztt/create", type="json", auth="user", methods=["POST"])
    def mp_create(self, **payload):
        params = request.env["ir.config_parameter"].sudo()
        token = params.get_param(PARAM_ACCESS_TOKEN, "")
        if not token:
            return {"error": "Faltan credenciales de Mercado Pago (Access Token)."}

        data = request.jsonrequest or {}
        amount, currency, order_ref = data.get("amount"), data.get("currency", "ARS"), data.get("order_ref")

        # TODO: completar endpoint de Mercado Pago QR Dinámico
        mp_url = "https://api.mercadopago.com/instore/orders/qr/seller/collectors/{collector_id}/pos/{pos_id}/qrs"
        body = {
            "title": f"POS Order {order_ref}",
            "description": "Pago QR POS",
            "external_reference": order_ref,
            "total_amount": amount,
            "items": [{"title": "POS", "unit_price": amount, "quantity": 1, "currency_id": currency}],
        }

        try:
            resp = requests.post(mp_url, headers=_mp_headers(token), data=json.dumps(body), timeout=20)
            resp.raise_for_status()
            mp = resp.json()
            return {
                "payment_id": mp.get("id"),
                "external_reference": mp.get("external_reference", order_ref),
                "qr_base64": mp.get("qr", ""),
                "qr_url": mp.get("qr_image", ""),
            }
        except requests.RequestException as e:
            _logger.exception("Error Mercado Pago")
            return {"error": str(e)}

    @http.route("/mp/mezztt/status/<string:payment_id>", type="json", auth="user", methods=["GET"])
    def mp_status(self, payment_id, **kw):
        token = request.env["ir.config_parameter"].sudo().get_param(PARAM_ACCESS_TOKEN, "")
        if not token:
            return {"error": "Faltan credenciales."}
        try:
            url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
            r = requests.get(url, headers=_mp_headers(token), timeout=15)
            r.raise_for_status()
            mp = r.json()
            return {"status": mp.get("status", "pending"), "raw": mp}
        except requests.RequestException as e:
            _logger.exception("Error status Mercado Pago")
            return {"error": str(e)}
