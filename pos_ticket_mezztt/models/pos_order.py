
from odoo import models, api, fields
import base64
import qrcode
from io import BytesIO

class PosOrder(models.Model):
    _inherit = 'pos.order'

    cae = fields.Char(string='CAE')
    cae_due_date = fields.Date(string='CAE Due Date')
    qr_afip_base64 = fields.Text(string="QR AFIP Base64")
    company_cuit = fields.Char(string="Company CUIT")
    pos_branch = fields.Char(string="Punto de Venta")

    @api.model
    def _process_order(self, order, draft=False, existing_order=False):
        order_id = super()._process_order(order, draft, existing_order)

        # Obtener la orden procesada
        pos_order = self.browse(order_id.id)

        # Generar factura
        if pos_order.session_id.config_id.invoice_journal_id:
            pos_order._create_invoice()

        # Obtener datos fiscales de la factura
        if pos_order.account_move:
            factura = pos_order.account_move
            pos_order.cae = factura.l10n_ar_cae
            pos_order.cae_due_date = factura.l10n_ar_cae_due
            pos_order.company_cuit = factura.company_id.vat
            pos_order.pos_branch = pos_order.session_id.config_id.name

            # Generar QR base64 desde URL de AFIP
            if factura.l10n_ar_afip_qr_code_url:
                qr = qrcode.make(factura.l10n_ar_afip_qr_code_url)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                pos_order.qr_afip_base64 = qr_base64

        return order_id
