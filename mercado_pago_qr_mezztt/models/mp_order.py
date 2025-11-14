# -*- coding: utf-8 -*-
"""Persistent storage for Mercado Pago in-store orders.

The webhook y polling comparten esta tabla para mantener el estado local de la
transacción.  Se mantiene lo más simple posible: solo se almacenan los datos
mínimos necesarios para correlacionar un pedido de POS con la orden de Mercado
Pago.
"""

from odoo import api, fields, models


class MercadoPagoQrOrder(models.Model):
    """Record linking a POS order with the Mercado Pago order id."""

    _name = "mercado.pago.qr.order"
    _description = "Mercado Pago POS QR order"
    _order = "create_date desc"

    pos_reference = fields.Char(
        string="Referencia POS",
        required=True,
        help=(
            "Identificador legible de la orden en Odoo POS.  Suele coincidir con "
            "order_uid o name, y permite depurar rápidamente cualquier incidencia."
        ),
    )
    mp_order_id = fields.Char(
        string="ID Mercado Pago",
        required=True,
        index=True,
        help="Valor devuelto por la API al crear la orden (por ejemplo ORD123...).",
    )
    status = fields.Selection(
        selection=[
            ("pending", "Pendiente"),
            ("approved", "Aprobado"),
            ("rejected", "Rechazado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="pending",
        required=True,
        help="Último estado conocido reportado por Mercado Pago.",
    )
    payload = fields.Text(
        string="Última respuesta",
        help="JSON con la última respuesta relevante recibida de Mercado Pago.",
    )

    _sql_constraints = [
        (
            "mp_order_unique",
            "unique(mp_order_id)",
            "La orden de Mercado Pago ya fue registrada.",
        )
    ]

    @api.model
    def register_order(self, pos_reference, mp_order_id, status="pending", payload=None):
        """Create or update an entry in the table.

        The controller layer utiliza este helper para evitar duplicados cuando
        se reciben notificaciones repetidas.
        """

        existing = self.search([("mp_order_id", "=", mp_order_id)], limit=1)
        values = {
            "pos_reference": pos_reference,
            "status": status,
        }
        if payload:
            values["payload"] = payload
        if existing:
            existing.write(values)
            return existing
        return self.create(dict(values, mp_order_id=mp_order_id))
