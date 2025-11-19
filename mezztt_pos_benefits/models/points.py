from odoo import api, fields, models


class PosLoyaltyPoints(models.Model):
    _name = "pos.loyalty_points"
    _description = "Sistema de puntos POS"
    _rec_name = "customer_id"

    customer_id = fields.Many2one("res.partner", string="Cliente", required=True)
    points = fields.Float(string="Puntos", default=0.0)
    updated_at = fields.Datetime(string="Actualizado", default=fields.Datetime.now)

    _sql_constraints = [
        (
            "pos_loyalty_points_unique_partner",
            "unique(customer_id)",
            "El cliente ya tiene un registro de puntos.",
        )
    ]

    def write(self, vals):
        vals["updated_at"] = fields.Datetime.now()
        return super().write(vals)

    @api.model
    def create(self, vals):
        vals.setdefault("updated_at", fields.Datetime.now())
        return super().create(vals)

    def add_points(self, points):
        for record in self:
            record.points += points
            record.updated_at = fields.Datetime.now()
        return True
