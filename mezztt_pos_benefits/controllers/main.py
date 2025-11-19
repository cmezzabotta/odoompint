from odoo import http
from odoo.http import request


class PosBenefitsController(http.Controller):

    @http.route(
        "/pos_benefits/validate_code",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def validate_code(self, code, type):
        if not code or type not in ("giftcard", "coupon"):
            return {"success": False, "error": "Parámetros inválidos."}

        model = "pos.giftcard" if type == "giftcard" else "pos.coupon"
        domain_field = "name" if type == "giftcard" else "code"
        domain = [(domain_field, "=", code)]

        record = request.env[model].sudo().search(domain, limit=1)
        if not record:
            return {"success": False, "error": "Código inválido."}

        data = {}
        if type == "giftcard":
            data = {
                "code": record.code,
                "amount": record.amount,
                "balance": record.balance,
                "state": record.state,
                "expiration_date": record.expiration_date,
            }
        else:
            data = {
                "code": record.code,
                "discount_type": record.discount_type,
                "discount_value": record.discount_value,
                "state": record.state,
                "expiration_date": record.expiration_date,
                "max_uses": record.max_uses,
                "used_count": record.used_count,
            }

        return {"success": True, "data": data}

    @http.route(
        "/pos_benefits/loyalty_points",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def get_loyalty_points(self, customer_id):
        if not customer_id:
            return {"success": False, "error": "Cliente no especificado."}

        record = (
            request.env["pos.loyalty_points"].sudo().search([("customer_id", "=", customer_id)], limit=1)
        )
        if not record:
            return {"success": True, "data": {"customer_id": customer_id, "points": 0}}

        return {
            "success": True,
            "data": {
                "customer_id": record.customer_id.id,
                "points": record.points,
                "updated_at": record.updated_at,
            },
        }
