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
    def validate_code(self, code=None, type=None, **kwargs):
        if not code or type not in ("giftcard", "coupon"):
            return {"success": False, "message": "Parámetros inválidos."}

        if type == "giftcard":
            record = request.env["pos.giftcard"].sudo().search([("code", "=", code)], limit=1)
            if not record:
                return {"success": False, "message": "Giftcard no encontrada."}
            try:
                record._ensure_available()
            except Exception as exc:  # pylint: disable=broad-except
                return {"success": False, "message": str(exc)}
            return {"success": True, "data": record.to_pos_dict()}

        record = request.env["pos.coupon"].sudo().search([("code", "=", code)], limit=1)
        if not record:
            return {"success": False, "message": "Cupón no encontrado."}
        try:
            record._ensure_available()
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "message": str(exc)}
        return {"success": True, "data": record.to_pos_dict()}

    @http.route(
        "/pos_benefits/loyalty_points",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def loyalty_points(self, customer_id=None, **kwargs):
        if not customer_id:
            return {"success": False, "message": "Cliente inválido."}
        record = request.env["pos.loyalty_points"].sudo().search(
            [("customer_id", "=", int(customer_id))], limit=1
        )
        if not record:
            return {"success": True, "data": None}
        return {
            "success": True,
            "data": {
                "id": record.id,
                "customer_id": record.customer_id.id,
                "points": record.points,
                "updated_at": record.updated_at,
            },
        }
