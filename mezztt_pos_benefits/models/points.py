from odoo import models, fields

class PosLoyaltyPoints(models.Model):
    _name = "pos.loyalty.points"
    _description = "Sistema de puntos POS"

    partner_id = fields.Many2one("res.partner")
    points = fields.Float(default=0)
