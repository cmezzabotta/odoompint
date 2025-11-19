from odoo import api, fields, models


class PosLoyaltyPoints(models.Model):
    _name = "pos.loyalty_points"
    _description = "Puntos de fidelidad para POS"
    _order = "customer_id"

    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        required=True,
        ondelete="cascade",
    )
    points = fields.Float(string="Puntos", default=0.0)
    updated_at = fields.Datetime(string="Última actualización", default=fields.Datetime.now)

    _sql_constraints = [
        ("pos_loyalty_unique_customer", "unique(customer_id)", "Cada cliente solo puede tener un registro de puntos."),
    ]

    def write(self, vals):
        if "points" in vals:
            vals.setdefault("updated_at", fields.Datetime.now())
        return super().write(vals)

    @api.model
    def create(self, vals):
        vals.setdefault("updated_at", fields.Datetime.now())
        return super().create(vals)

    @api.model
    def get_points_for_customer(self, customer_id):
        record = self.sudo().search([("customer_id", "=", customer_id)], limit=1)
        return record.read(["id", "customer_id", "points", "updated_at"])
