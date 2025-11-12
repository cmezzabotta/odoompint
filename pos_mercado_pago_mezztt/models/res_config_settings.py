from odoo import api, fields, models

PARAM_ACCESS_TOKEN = "pos_mercado_pago_mezztt.access_token"
PARAM_PUBLIC_KEY = "pos_mercado_pago_mezztt.public_key"
PARAM_SANDBOX = "pos_mercado_pago_mezztt.sandbox"

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mp_access_token = fields.Char(string="Mercado Pago Access Token")
    mp_public_key = fields.Char(string="Mercado Pago Public Key")
    mp_sandbox = fields.Boolean(string="Usar Sandbox")

    def set_values(self):
        super().set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param(PARAM_ACCESS_TOKEN, self.mp_access_token or "")
        icp.set_param(PARAM_PUBLIC_KEY, self.mp_public_key or "")
        icp.set_param(PARAM_SANDBOX, "1" if self.mp_sandbox else "0")

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"].sudo()
        res.update(
            mp_access_token=icp.get_param(PARAM_ACCESS_TOKEN, default=""),
            mp_public_key=icp.get_param(PARAM_PUBLIC_KEY, default=""),
            mp_sandbox=icp.get_param(PARAM_SANDBOX, default="0") == "1"
        )
        return res
