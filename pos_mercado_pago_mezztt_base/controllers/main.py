import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MercadoPagoMezzttController(http.Controller):
    def _service(self):
        return request.env["pos.mercado_pago_mezztt.service"].sudo()

    @http.route("/mp/mezztt/test", auth="public", type="http", csrf=False)
    def test(self):
        return "Modulo POS Mercado Pago _mezztt operativo"

    @http.route(
        "/mp/mezztt/create_order",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def create_order(self, amount, currency, order_reference, payment_method_id, description=None):
        service = self._service()
        data = service.create_qr_order(
            amount=float(amount),
            currency=currency,
            order_reference=order_reference,
            payment_method_id=int(payment_method_id) if payment_method_id else 0,
            description=description,
        )
        _logger.info("Orden Mercado Pago QR creada %s", data.get("external_reference"))
        return data

    @http.route(
        "/mp/mezztt/payment_status",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def payment_status(self, external_reference, payment_method_id, payment_id=None):
        service = self._service()
        status = service.get_payment_status(
            external_reference=external_reference,
            payment_method_id=int(payment_method_id) if payment_method_id else 0,
        )
        if payment_id and status.get("status") == "pending":
            details = service.get_payment_details(payment_id, int(payment_method_id) if payment_method_id else 0)
            status.update(details)
        return status

    @http.route(
        "/mp/mezztt/webhook",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def webhook(self, **payload):
        _logger.info("Webhook Mercado Pago recibido: %s", payload)
        return {"received": True}
