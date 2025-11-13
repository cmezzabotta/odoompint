# -*- coding: utf-8 -*-
"""Extensions for POS order to support Mercado Pago QR integration."""

import base64
import json
from datetime import datetime, time

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        data = super()._payment_fields(order, ui_paymentline)
        if ui_paymentline.get("mp_payment_id"):
            data["mp_payment_id"] = ui_paymentline["mp_payment_id"]
        if ui_paymentline.get("mp_external_reference"):
            data["mp_external_reference"] = ui_paymentline["mp_external_reference"]
        if ui_paymentline.get("mp_transaction_id"):
            data["mp_transaction_id"] = ui_paymentline["mp_transaction_id"]
        return data

    @api.model
    def _export_for_ui(self, order):
        export = super()._export_for_ui(order)
        export["fiscal_qr_url"] = order._get_fiscal_qr_url()
        return export

    def _get_fiscal_qr_url(self):
        self.ensure_one()
        move = self.account_move or self.invoice_id
        if not move:
            return False
        qr_url = getattr(move, "l10n_ar_afip_qr_code_url", False)
        if qr_url:
            return qr_url
        qr_code = getattr(move, "l10n_ar_afip_qr_code", False)
        if qr_code:
            if qr_code.startswith("http"):
                return qr_code
            return f"https://www.afip.gob.ar/fe/qr/?p={qr_code}"
        payload = self._build_fiscal_qr_payload(move)
        if not payload:
            return False
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")
        return f"https://www.afip.gob.ar/fe/qr/?p={encoded}"

    def _build_fiscal_qr_payload(self, move):
        company = move.company_id
        partner = move.commercial_partner_id
        currency = move.currency_id or company.currency_id
        doc_type = getattr(move, "l10n_latam_document_type_id", False)
        try:
            doc_type_code = int(getattr(doc_type, "code", 99)) if doc_type else 99
        except (TypeError, ValueError):
            doc_type_code = 99
        nro_doc_rec = partner.vat or getattr(partner, "l10n_latam_identification_number", None) or "0"
        nro_doc_rec = "".join(filter(str.isdigit, nro_doc_rec)) or "0"

        partner_doc_type = getattr(partner, "l10n_latam_identification_type_id", False)
        partner_doc_code = 99
        if partner_doc_type:
            for attr in ("l10n_ar_code", "code"):
                value = getattr(partner_doc_type, attr, False)
                if not value:
                    continue
                try:
                    partner_doc_code = int(value)
                    break
                except (TypeError, ValueError):
                    continue

        journal_pos = getattr(move.journal_id, "l10n_ar_afip_pos_number", 0) or 0
        auth_code = getattr(move, "l10n_ar_afip_auth_code", False)
        try:
            auth_code_value = int(auth_code) if auth_code else 0
        except ValueError:
            auth_code_value = 0

        invoice_date = move.invoice_date or fields.Date.context_today(move)
        if isinstance(invoice_date, datetime):
            dt_value = invoice_date
        else:
            dt_value = datetime.combine(invoice_date, time.min)

        document_number = getattr(move, "l10n_latam_document_number", False) or move.name or "0"
        document_number = "".join(filter(str.isdigit, document_number)) or "0"

        company_vat = company.vat or "0"
        company_vat = "".join(filter(str.isdigit, company_vat)) or "0"

        payload = {
            "ver": 1,
            "fecha": dt_value.strftime("%Y-%m-%dT%H:%M:%S"),
            "cuit": int(company_vat[-11:]) if company_vat else 0,
            "ptoVta": int(journal_pos),
            "tipoCmp": doc_type_code,
            "nroCmp": int(document_number),
            "importe": float(move.amount_total or 0.0),
            "moneda": currency.name or "ARS",
            "ctz": float(getattr(move, "currency_rate", 1.0) or 1.0),
            "tipoDocRec": partner_doc_code,
            "nroDocRec": int(nro_doc_rec),
            "tipoCodAut": "E" if getattr(move, "l10n_ar_afip_auth_mode", "") == "E" else "A",
            "codAut": auth_code_value,
        }
        return payload
