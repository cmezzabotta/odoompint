import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosGiftCard(models.Model):
    _name = "pos.giftcard"
    _description = "Giftcard para Punto de Venta"
    _order = "code desc"

    code = fields.Char(
        string="Código",
        required=True,
        copy=False,
        default=lambda self: uuid.uuid4().hex[:12].upper(),
    )
    name = fields.Char(string="Nombre", compute="_compute_name", store=True, index=True)
    amount = fields.Float(string="Monto emitido", required=True, default=0.0)
    balance = fields.Float(string="Saldo actual", required=True, default=0.0)
    expiration_date = fields.Date(string="Fecha de vencimiento")
    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("used", "Utilizada"),
            ("expired", "Vencida"),
        ],
        default="draft",
        required=True,
    )
    notes = fields.Text(string="Notas")
    pos_order_ids = fields.Many2many(
        comodel_name="pos.order",
        relation="pos_giftcard_order_rel",
        column1="giftcard_id",
        column2="order_id",
        string="Órdenes de POS",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("pos_giftcard_code_unique", "unique(code)", "El código de la giftcard debe ser único."),
    ]

    @api.depends("code")
    def _compute_name(self):
        for record in self:
            record.name = record.code

    @api.model
    def create(self, vals):
        vals = vals.copy()
        vals.setdefault("balance", vals.get("amount", 0.0))
        state = vals.get("state") or "draft"
        vals.setdefault("active", state == "active")
        return super().create(vals)

    def write(self, vals):
        vals = vals.copy()
        if "state" in vals and "active" not in vals:
            vals["active"] = vals["state"] == "active"
        return super().write(vals)

    def _ensure_available(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "active":
                raise UserError(_("La giftcard no está activa."))
            if record.expiration_date and record.expiration_date < today:
                record.write({"state": "expired", "active": False})
                raise UserError(_("La giftcard está vencida."))
            if record.balance <= 0:
                record.write({"state": "used", "active": False})
                raise UserError(_("La giftcard no tiene saldo disponible."))

    def consume_amount(self, amount):
        self.ensure_one()
        if amount <= 0:
            raise UserError(_("El monto a consumir debe ser positivo."))
        self._ensure_available()
        if self.balance < amount:
            raise UserError(_("La giftcard no tiene saldo suficiente."))
        new_balance = self.balance - amount
        new_state = "used" if new_balance <= 0 else "active"
        vals = {"balance": new_balance, "state": new_state}
        if new_state == "used":
            vals["active"] = False
        self.write(vals)

    def to_pos_dict(self):
        self.ensure_one()
        return {
            "id": self.id,
            "code": self.code,
            "amount": self.amount,
            "balance": self.balance,
            "expiration_date": self.expiration_date,
            "state": self.state,
            "notes": self.notes,
        }
