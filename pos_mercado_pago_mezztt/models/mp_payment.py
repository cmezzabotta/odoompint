from odoo import fields, models


class PosMercadoPagoMezzttPayment(models.Model):
    _name = "pos.mercado_pago.mezztt.payment"
    _description = "Mercado Pago POS QR Payment (mezztt)"
    _order = "create_date desc"
    _rec_name = "payment_id"

    payment_id = fields.Char(required=True, index=True)
    external_reference = fields.Char()
    pos_session_id = fields.Many2one("pos.session", ondelete="set null")
    amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency")
    status = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
    )
    details = fields.Text()
    last_sync_at = fields.Datetime()

    def update_from_mp_response(self, mp_payload):
        self.ensure_one()
        status = mp_payload.get("status", "pending") if isinstance(mp_payload, dict) else "pending"
        values = {
            "status": status,
            "details": self._serialize_payload(mp_payload),
            "last_sync_at": fields.Datetime.now(),
        }
        external_reference = mp_payload.get("external_reference") if isinstance(mp_payload, dict) else None
        if external_reference:
            values["external_reference"] = external_reference
        self.write(
            values
        )

    @staticmethod
    def _serialize_payload(payload):
        if not payload:
            return False
        if isinstance(payload, str):
            return payload
        try:
            import json

            return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception:  # pragma: no cover - defensive
            return str(payload)

    @classmethod
    def upsert_payment(cls, values):
        payment = cls.sudo().search([("payment_id", "=", values.get("payment_id"))], limit=1)
        if payment:
            payment.write(values)
        else:
            payment = cls.sudo().create(values)
        return payment
