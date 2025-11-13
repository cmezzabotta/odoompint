# -*- coding: utf-8 -*-
"""Persist Mercado Pago metadata on POS payments."""

from odoo import api, fields, models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    mp_transaction_id = fields.Many2one("pos.mp.qr.transaction", string="Transacción Mercado Pago", readonly=True)
    mp_payment_id = fields.Char(string="ID pago Mercado Pago", readonly=True)
    mp_external_reference = fields.Char(string="Referencia externa Mercado Pago", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        for payment, vals in zip(payments, vals_list):
            transaction = False
            transaction_id = vals.get("mp_transaction_id") if isinstance(vals, dict) else False
            if transaction_id:
                transaction = self.env["pos.mp.qr.transaction"].browse(transaction_id)
            if not transaction and payment.mp_external_reference:
                transaction = self.env["pos.mp.qr.transaction"].search(
                    [("external_reference", "=", payment.mp_external_reference)], limit=1
                )
            if transaction:
                transaction.write(
                    {
                        "status": "approved" if payment.amount > 0 else transaction.status,
                        "payment_id": payment.mp_payment_id or transaction.payment_id,
                        "pos_payment_id": payment.id,
                    }
                )
                payment.mp_transaction_id = transaction.id
        return payments
