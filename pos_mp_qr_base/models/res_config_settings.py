# -*- coding: utf-8 -*-
"""Settings for Mercado Pago QR POS integration."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mercadopago_access_token = fields.Char(config_parameter="pos_mp_qr_base.mercadopago_access_token")
    mercadopago_timeout_seconds = fields.Integer(
        string="Tiempo máximo de espera (segundos)",
        config_parameter="pos_mp_qr_base.timeout_seconds",
        default=180,
        help="Tiempo máximo que el POS esperará una respuesta de Mercado Pago antes de cancelar el pago.",
    )
