from odoo import models, fields
from odoo.exceptions import UserError
import uuid

class PosGiftCard(models.Model):
    _name = "pos.giftcard"
    _description = "GiftCard POS"

    name = fields.Char("Código", default=lambda s: uuid.uuid4().hex[:12].upper(), required=True)
    balance = fields.Float("Saldo disponible", required=True)
    active = fields.Boolean(default=True)

    def consume_amount(self, amount):
        if self.balance < amount:
            raise UserError("La giftcard no tiene saldo suficiente.")
        self.balance -= amount
        if self.balance <= 0:
            self.active = False
