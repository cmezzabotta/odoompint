
from odoo import models, fields

class PosConfig(models.Model):
    _inherit = "pos.config"

    mp_public_key = fields.Char("MP Public Key")
    mp_access_token = fields.Char("MP Access Token")
    mp_store_id = fields.Char("Store ID")
    mp_external_store_id = fields.Char("External Store ID")
    mp_pos_id = fields.Char("POS ID")
    mp_external_pos_id = fields.Char("External POS ID")
    mp_static_qr_url = fields.Char("Static QR URL")
