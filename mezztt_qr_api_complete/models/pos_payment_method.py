import json
import logging
from typing import Any, Dict

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    mp_qr_enabled = fields.Boolean(
        string="Mercado Pago QR Estático",
        help="Activa la integración con Mercado Pago usando códigos QR estáticos.",
    )
    mp_access_token = fields.Char(string="Access Token", groups="point_of_sale.group_pos_manager")
    mp_public_key = fields.Char(string="Public Key", groups="point_of_sale.group_pos_manager")
    mp_store_id = fields.Char(string="Store ID", groups="point_of_sale.group_pos_manager")
    mp_pos_id = fields.Char(string="POS ID", groups="point_of_sale.group_pos_manager")
    mp_external_pos_id = fields.Char(string="External POS ID", groups="point_of_sale.group_pos_manager")
    mp_qr_static = fields.Char(
        string="QR Estático",
        help="URL del QR estático provisto por Mercado Pago.",
        groups="point_of_sale.group_pos_manager",
    )

    # ------------------------------------------------------------------
    # Terminal wiring
    # ------------------------------------------------------------------
    def _get_payment_terminal_selection(self):
        selection = list(super()._get_payment_terminal_selection())
        terminal = ("mercado_pago_qr_static", "Mercado Pago QR Estático")
        if terminal not in selection:
            selection.append(terminal)
        return selection

    @api.depends("mp_qr_enabled")
    def _compute_type(self):
        super()._compute_type()
        for method in self:
            if method.mp_qr_enabled and method.type != "bank":
                method.type = "bank"

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        fields_list += [
            "mp_qr_enabled",
            "mp_access_token",
            "mp_public_key",
            "mp_store_id",
            "mp_pos_id",
            "mp_external_pos_id",
            "mp_qr_static",
        ]
        return fields_list

    def write(self, vals):
        vals = dict(vals)
        if vals.get("use_payment_terminal") == "mercado_pago_qr_static":
            vals.setdefault("mp_qr_enabled", True)
        res = super().write(vals)
        if (
            not self.env.context.get("mpqr_static_skip_terminal")
            and ("mp_qr_enabled" in vals or vals.get("use_payment_terminal") == "mercado_pago_qr_static")
        ):
            for method in self:
                if method.mp_qr_enabled:
                    method.with_context(mpqr_static_skip_terminal=True).write({
                        "use_payment_terminal": "mercado_pago_qr_static",
                        "payment_method_type": "terminal",
                    })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        cleaned_vals = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get("use_payment_terminal") == "mercado_pago_qr_static":
                vals.setdefault("mp_qr_enabled", True)
            cleaned_vals.append(vals)
        records = super().create(cleaned_vals)
        for method, vals in zip(records, cleaned_vals):
            if vals.get("mp_qr_enabled") or vals.get("use_payment_terminal") == "mercado_pago_qr_static":
                method.with_context(mpqr_static_skip_terminal=True).write({
                    "use_payment_terminal": "mercado_pago_qr_static",
                    "payment_method_type": "terminal",
                })
        return records

    @api.constrains(
        "mp_qr_enabled",
        "mp_access_token",
        "mp_store_id",
        "mp_pos_id",
        "mp_external_pos_id",
        "mp_qr_static",
    )
    def _check_mp_configuration(self):
        required = {
            "mp_access_token": _("Access Token"),
            "mp_store_id": _("Store ID"),
            "mp_pos_id": _("POS ID"),
            "mp_external_pos_id": _("External POS ID"),
            "mp_qr_static": _("Static QR"),
        }
        for method in self.filtered("mp_qr_enabled"):
            missing = [label for field_name, label in required.items() if not getattr(method, field_name)]
            if missing:
                raise ValidationError(
                    _("Los siguientes campos son obligatorios para Mercado Pago QR: %s")
                    % ", ".join(missing)
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _mpqr_headers(self):
        self.ensure_one()
        return {
            "Authorization": f"Bearer {self.mp_access_token}",
            "Content-Type": "application/json",
        }

    def _ensure_mp_credentials(self):
        self.ensure_one()
        if not self.mp_qr_enabled:
            raise UserError(_("Este método de pago no usa Mercado Pago QR estático."))
        for field_name in ("mp_access_token", "mp_store_id", "mp_pos_id", "mp_external_pos_id"):
            if not getattr(self, field_name):
                raise UserError(_("El campo %s es obligatorio para operar con Mercado Pago.") % field_name)

    def _prepare_static_payload(self, order_vals: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_one()
        amount = round(float(order_vals.get("amount", 0.0)), 2)
        if amount <= 0:
            raise UserError(_("El monto del pago debe ser mayor a cero."))
        payload = {
            "external_reference": order_vals.get("reference"),
            "title": order_vals.get("title") or order_vals.get("reference"),
            "description": order_vals.get("description") or order_vals.get("reference"),
            "amount": amount,
            "store_id": self.mp_store_id,
            "pos_id": self.mp_pos_id,
            "external_pos_id": self.mp_external_pos_id,
        }
        customer_data = {}
        if order_vals.get("customer_name"):
            customer_data["name"] = order_vals["customer_name"]
        if order_vals.get("customer_email"):
            customer_data["email"] = order_vals["customer_email"]
        if customer_data:
            payload["customer"] = customer_data
        return payload

    # ------------------------------------------------------------------
    # API entry points used by the POS
    # ------------------------------------------------------------------
    def mpqr_static_create_order(self, order_vals):
        self.ensure_one()
        payment_method = self.sudo()
        payment_method._ensure_mp_credentials()
        payload = payment_method._prepare_static_payload(order_vals)
        url = f"https://api.mercadopago.com/instore/orders/qr/{payment_method.mp_pos_id}"
        try:
            response = requests.post(url, json=payload, headers=payment_method._mpqr_headers(), timeout=30)
        except requests.RequestException as err:
            _logger.exception("Mercado Pago QR request failed")
            raise UserError(_("No se pudo crear la orden en Mercado Pago. %s") % err) from err
        data = payment_method._handle_response(response, "create order")
        return {
            "id": data.get("id"),
            "status": data.get("status"),
            "external_reference": data.get("external_reference"),
        }

    def mpqr_static_poll(self, order_id):
        self.ensure_one()
        payment_method = self.sudo()
        payment_method._ensure_mp_credentials()
        url = f"https://api.mercadopago.com/instore/merchant/orders/{order_id}"
        try:
            response = requests.get(url, headers=payment_method._mpqr_headers(), timeout=30)
        except requests.RequestException as err:
            _logger.exception("Mercado Pago QR polling failed")
            raise UserError(_("No se pudo consultar el estado del pago en Mercado Pago. %s") % err) from err
        data = payment_method._handle_response(response, "check order")
        payments = data.get("payments") or []
        payment_status = next((p.get("status") for p in payments if p.get("status")), "")
        payment_status = (payment_status or "").lower()
        status = (data.get("status") or "pending").lower()
        if payment_status == "approved" or data.get("status_detail") == "approved":
            result_status = "approved"
        elif payment_status in {"rejected", "cancelled"}:
            result_status = payment_status
        elif status in {"rejected", "cancelled", "expired"}:
            result_status = status
        else:
            result_status = "pending"
        return {
            "status": result_status,
            "raw_status": status,
            "payments": payments,
            "detail": data,
        }

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    def _handle_response(self, response, action):
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code >= 400 or data.get("error"):
            message = data.get("message") or data.get("error") or response.reason
            raise UserError(
                _("Mercado Pago devolvió un error al %s: %s") % (action, message)
            )
        _logger.debug("Mercado Pago response (%s): %s", action, json.dumps(data))
        return data
