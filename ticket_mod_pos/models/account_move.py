# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    is_pos_invoice = fields.Boolean(
        string="Factura de POS",
        compute="_compute_is_pos_invoice",
        store=False
    )

    @api.depends("invoice_origin", "journal_id")
    def _compute_is_pos_invoice(self):
        """
        Heurística no intrusiva:
        - Si existe el campo pos_order_id (algunas versiones/instalaciones lo agregan), úsalo.
        - Si no existe, usa invoice_origin iniciando con 'POS ' o 'POS/' como indicio fuerte.
        - Mantiene compatibilidad con cualquier diario de ventas.
        """
        # Detectar si el campo existe en el modelo (evita excepciones en distintas versiones)
        has_pos_order_field = "pos_order_id" in self._fields

        for move in self:
            flag = False
            try:
                if has_pos_order_field and getattr(move, "pos_order_id", False):
                    flag = True
                elif move.invoice_origin:
                    origin = (move.invoice_origin or "").strip().upper()
                    # Casos comunes de origen: "POS/0001-00000012" o "POS 0001-00000012"
                    if origin.startswith("POS/") or origin.startswith("POS "):
                        flag = True
            except Exception:
                flag = False
            move.is_pos_invoice = bool(flag)
