# -*- coding: utf-8 -*-
"""Extension of POS payment methods to flag Mercado Pago QR usage."""

from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    mp_use_qr = fields.Boolean(
        string="Usar Mercado Pago QR",
        help="Si está activo, este método de pago disparará la integración QR de Mercado Pago.",
    )
