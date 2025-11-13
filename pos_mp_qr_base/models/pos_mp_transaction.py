# -*- coding: utf-8 -*-
"""Model to track Mercado Pago QR transactions from the POS."""

from odoo import fields, models


class PosMercadoPagoTransaction(models.Model):
    _name = "pos.mp.qr.transaction"
    _description = "Transacción QR Mercado Pago"
    _order = "id desc"

    name = fields.Char(required=True)
    external_reference = fields.Char(required=True, index=True)
    preference_id = fields.Char(string="ID Preferencia")
    order_uid = fields.Char(string="UID Orden POS")
    pos_session_id = fields.Many2one("pos.session", string="Sesión POS")
    amount = fields.Float()
    currency_name = fields.Char()
    status = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("approved", "Aprobado"),
            ("cancelled", "Cancelado"),
        ],
        default="pending",
        required=True,
    )
    payment_id = fields.Char(string="ID pago MP")
    last_status_detail = fields.Char()
    qr_init_point = fields.Char(string="Enlace QR")
    qr_base64 = fields.Text(string="Imagen QR Base64")
    expiration_at = fields.Datetime()
    pos_payment_id = fields.Many2one("pos.payment", string="Pago POS")
