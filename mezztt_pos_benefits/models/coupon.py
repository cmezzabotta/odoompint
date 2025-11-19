from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosCoupon(models.Model):
    _name = "pos.coupon"
    _description = "Cupón de descuento para POS"
    _order = "code desc"

    code = fields.Char(string="Código", required=True, copy=False)
    discount_type = fields.Selection(
        selection=[("percent", "Porcentaje"), ("fixed", "Monto fijo")],
        string="Tipo de descuento",
        required=True,
        default="percent",
    )
    type = fields.Selection(
        selection=[("percent", "Porcentaje"), ("fixed", "Monto fijo")],
        related="discount_type",
        readonly=True,
        store=True,
    )
    discount_value = fields.Float(string="Valor", required=True, default=0.0)
    value = fields.Float(related="discount_value", readonly=True, store=True)
    expiration_date = fields.Date(string="Fecha de vencimiento")
    max_uses = fields.Integer(string="Máximo de usos")
    used_count = fields.Integer(string="Usos realizados", default=0, readonly=True)
    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("active", "Activo"),
            ("expired", "Vencido"),
        ],
        default="draft",
        required=True,
    )
    notes = fields.Text(string="Notas")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("pos_coupon_code_unique", "unique(code)", "El código del cupón debe ser único."),
    ]

    @api.constrains("discount_type", "discount_value")
    def _check_discount_value(self):
        for record in self:
            if record.discount_value <= 0:
                raise UserError(_("El valor del descuento debe ser positivo."))
            if record.discount_type == "percent" and record.discount_value > 100:
                raise UserError(_("El descuento porcentual no puede superar el 100%."))

    def write(self, vals):
        vals = vals.copy()
        if "state" in vals and "active" not in vals:
            vals["active"] = vals["state"] == "active"
        return super().write(vals)

    @api.model
    def create(self, vals):
        vals = vals.copy()
        state = vals.get("state") or "draft"
        vals.setdefault("active", state == "active")
        return super().create(vals)

    def _ensure_available(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "active" or not record.active:
                raise UserError(_("El cupón no está activo."))
            if record.expiration_date and record.expiration_date < today:
                record.write({"state": "expired", "active": False})
                raise UserError(_("El cupón está vencido."))
            if record.max_uses and record.used_count >= record.max_uses:
                raise UserError(_("El cupón alcanzó el máximo de usos."))

    def register_use(self):
        for record in self:
            record._ensure_available()
            new_count = record.used_count + 1
            vals = {"used_count": new_count}
            if record.max_uses and new_count >= record.max_uses:
                vals["state"] = "expired"
            record.write(vals)

    def to_pos_dict(self):
        self.ensure_one()
        return {
            "id": self.id,
            "code": self.code,
            "discount_type": self.discount_type,
            "discount_value": self.discount_value,
            "expiration_date": self.expiration_date,
            "max_uses": self.max_uses,
            "used_count": self.used_count,
            "state": self.state,
            "notes": self.notes,
        }
