from odoo import api, fields, models
from odoo.exceptions import UserError
import uuid


class PosGiftCard(models.Model):
    _name = "pos.giftcard"
    _description = "Gift Card"
    _rec_name = "code"
    _order = "create_date desc"

    code = fields.Char(
        string="Código",
        required=True,
        copy=False,
        index=True,
        default=lambda self: uuid.uuid4().hex[:12].upper(),
    )
    name = fields.Char(string="Nombre", related="code", store=True, readonly=True)
    amount = fields.Float(string="Monto", required=True, default=0.0)
    balance = fields.Float(string="Saldo disponible", required=True, default=0.0)
    active = fields.Boolean(default=True)
    expiration_date = fields.Date(string="Fecha de vencimiento")
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("used", "Utilizada"),
            ("expired", "Vencida"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Notas")
    pos_order_ids = fields.Many2many(
        comodel_name="pos.order",
        relation="pos_order_giftcard_rel",
        column1="giftcard_id",
        column2="order_id",
        string="Órdenes de POS",
        readonly=True,
    )

    _sql_constraints = [
        ("pos_giftcard_code_unique", "unique(code)", "El código de la giftcard debe ser único."),
    ]

    @api.model
    def create(self, vals):
        vals.setdefault("balance", vals.get("amount", 0.0))
        record = super().create(vals)
        record._update_state()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._update_state()
        return res

    def _update_state(self):
        today = fields.Date.today()
        for record in self:
            if record.state == "draft" and record.balance > 0:
                record.state = "active"
            if record.expiration_date and record.expiration_date < today:
                record.state = "expired"
            if record.balance <= 0 and record.state not in ("used", "expired"):
                record.state = "used"
            record.active = record.state not in ("used", "expired")

    def consume_amount(self, amount):
        for record in self:
            if record.state not in ("active", "draft"):
                raise UserError("La giftcard no está activa.")
            if record.expiration_date and record.expiration_date < fields.Date.today():
                record.state = "expired"
                raise UserError("La giftcard está vencida.")
            if record.balance < amount:
                raise UserError("La giftcard no tiene saldo suficiente.")
            record.balance -= amount
            if record.balance <= 0:
                record.state = "used"
            if record.state in ("used", "expired"):
                record.active = False
        return True
