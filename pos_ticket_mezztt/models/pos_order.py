
import base64
import logging
import re
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import qrcode
except Exception:  # pragma: no cover - fallback when optional lib is missing
    qrcode = None

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    cae = fields.Char(string="CAE")
    cae_due_date = fields.Date(string="CAE Due Date")
    qr_afip_base64 = fields.Text(string="QR AFIP Base64")
    company_cuit = fields.Char(string="Company CUIT")
    pos_branch = fields.Char(string="Punto de Venta")
    customer_vat_condition = fields.Char(string="Condición IVA del cliente")
    fiscal_error_message = fields.Text(string="Mensaje de error fiscal")

    @api.model
    def _process_order(self, order, existing_order=False):
        pos_orders = super()._process_order(order, existing_order=existing_order)

        if isinstance(pos_orders, models.Model):
            orders_to_process = pos_orders
        elif isinstance(pos_orders, (int, list, tuple)):
            orders_to_process = self.browse(pos_orders)
        else:  # pragma: no cover - defensive fallback
            orders_to_process = self.browse([])

        for pos_order in orders_to_process:
            pos_order._handle_fiscal_flow()

        return pos_orders

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------
    def _handle_fiscal_flow(self):
        for order in self:
            order._reset_fiscal_information()
            try:
                invoice = order._ensure_afip_invoice()
                order._fill_fiscal_data_from_invoice(invoice)
                order._mark_as_invoiced(invoice)
            except UserError as exc:
                order.write({"fiscal_error_message": str(exc)})
                _logger.warning("No se pudo emitir el ticket fiscal para %s: %s", order.name, exc)
            except Exception as exc:  # pragma: no cover - unexpected errors are logged
                order.write(
                    {
                        "fiscal_error_message": _(
                            "Error inesperado al emitir el ticket fiscal. Por favor reintente desde el backend.\nDetalle: %s"
                        )
                        % exc
                    }
                )
                _logger.exception("Unexpected error while generating AFIP invoice for POS order %s", order.name)

    def _reset_fiscal_information(self):
        self.write(
            {
                "cae": False,
                "cae_due_date": False,
                "qr_afip_base64": False,
                "company_cuit": False,
                "pos_branch": False,
                "customer_vat_condition": False,
                "fiscal_error_message": False,
            }
        )

    def _ensure_afip_invoice(self):
        self.ensure_one()
        config = self.session_id.config_id
        if not config or not config.invoice_journal_id:
            raise UserError(
                _(
                    "El TPV no tiene configurado un diario de facturación. Configurelo para poder emitir ticket fiscal."
                )
            )

        invoice = self.account_move
        if not invoice:
            invoice = self._create_invoice()

        if invoice.state != "posted":
            invoice.action_post()

        if hasattr(invoice, "_l10n_ar_edi_action_request_cae") and not invoice.l10n_ar_cae:
            invoice._l10n_ar_edi_action_request_cae()

        invoice.flush_recordset()
        return invoice

    def _fill_fiscal_data_from_invoice(self, invoice):
        self.ensure_one()
        if not invoice:
            return

        cae = invoice.l10n_ar_cae
        if not cae:
            raise UserError(
                _(
                    "La AFIP no devolvió un CAE válido para la factura %s. Revise la configuración fiscal y reintente."
                )
                % invoice.display_name
            )

        company_cuit = invoice.company_id.vat or ""
        company_cuit = re.sub(r"\D", "", company_cuit)
        company_cuit = company_cuit or False

        branch = (
            invoice.l10n_ar_afip_pos_number
            if hasattr(invoice, "l10n_ar_afip_pos_number") and invoice.l10n_ar_afip_pos_number
            else self.session_id.config_id.l10n_ar_afip_pos_number
        )
        branch = branch or self.session_id.config_id.name
        if branch:
            branch = str(branch)

        qr_base64 = False
        if invoice.l10n_ar_afip_qr_code_url:
            qr_base64 = self._generate_qr_base64(invoice.l10n_ar_afip_qr_code_url)

        partner_condition = self.partner_id.l10n_ar_afip_responsability_type_id.display_name if self.partner_id else False

        self.write(
            {
                "cae": cae,
                "cae_due_date": invoice.l10n_ar_cae_due,
                "qr_afip_base64": qr_base64,
                "company_cuit": company_cuit,
                "pos_branch": branch,
                "customer_vat_condition": partner_condition,
                "fiscal_error_message": False,
            }
        )

    def _mark_as_invoiced(self, invoice):
        """Ensure the POS order reflects an invoiced state when a fiscal invoice exists."""

        self.ensure_one()
        values = {}
        if invoice and not self.account_move:
            values["account_move"] = invoice.id

        if invoice and self.state != "invoiced":
            values["state"] = "invoiced"

        if values:
            self.write(values)

    def _generate_qr_base64(self, qr_url):
        if not qr_url:
            return False
        if not qrcode:
            _logger.warning("Python package qrcode is not installed. Unable to render AFIP QR image.")
            raise UserError(
                _(
                    "No se pudo generar el código QR fiscal porque falta la librería 'qrcode' en el servidor."
                )
            )

        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
