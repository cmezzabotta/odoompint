from odoo import models, fields
from odoo.exceptions import UserError

class PosCoupon(models.Model):
    _name = "pos.coupon"
    _description = "Cupón POS"

    code = fields.Char(required=True)
    type = fields.Selection([
        ("fixed", "Monto fijo"),
        ("percent", "Porcentaje"),
    ], required=True)
    value = fields.Float("Valor")
    active = fields.Boolean(default=True)
    expiration_date = fields.Date("Fecha de vencimiento")

    def validate_coupon(self):
        if not self.active:
            raise UserError("El cupón no está activo.")
        if self.expiration_date and self.expiration_date < fields.Date.today():
            raise UserError("El cupón está vencido.")
