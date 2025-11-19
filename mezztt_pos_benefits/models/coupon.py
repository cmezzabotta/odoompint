from odoo import api, fields, models
from odoo.exceptions import UserError


class PosCoupon(models.Model):
    _name = "pos.coupon"
    _description = "Cupón de descuento"
    _order = "create_date desc"

    code = fields.Char(string="Código", required=True, copy=False, index=True)
    discount_type = fields.Selection(
        [("percent", "Porcentaje"), ("fixed", "Monto fijo")],
        string="Tipo de descuento",
        required=True,
        default="fixed",
    )
    discount_value = fields.Float(string="Valor", required=True, default=0.0)
    type = fields.Selection(related="discount_type", store=True, readonly=True)
    value = fields.Float(related="discount_value", store=True, readonly=True)
    expiration_date = fields.Date(string="Fecha de vencimiento")
    max_uses = fields.Integer(string="Usos máximos", default=1)
    used_count = fields.Integer(string="Usos realizados", default=0, readonly=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("active", "Activo"), ("expired", "Vencido")],
        string="Estado",
        default="draft",
    )
    notes = fields.Text(string="Notas")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("pos_coupon_code_unique", "unique(code)", "El código del cupón debe ser único."),
    ]

    @api.model
    def create(self, vals):
        coupon = super().create(vals)
        coupon._update_state()
        return coupon

    def write(self, vals):
        res = super().write(vals)
        self._update_state()
        return res

    def _update_state(self):
        today = fields.Date.today()
        for record in self:
            if record.expiration_date and record.expiration_date < today:
                record.state = "expired"
            elif record.state == "draft":
                record.state = "active"
            record.active = record.state == "active"

    def validate_coupon(self):
        today = fields.Date.today()
        for record in self:
            if record.state != "active":
                raise UserError("El cupón no está activo.")
            if record.expiration_date and record.expiration_date < today:
                record.state = "expired"
                raise UserError("El cupón está vencido.")
            if record.max_uses and record.used_count >= record.max_uses:
                raise UserError("El cupón ya alcanzó el máximo de usos.")
        return True

    def mark_used(self):
        for record in self:
            record.used_count += 1
            if record.max_uses and record.used_count >= record.max_uses:
                record.state = "expired"
            record.active = record.state == "active"
        return True
