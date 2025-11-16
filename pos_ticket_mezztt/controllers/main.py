
from odoo import http
from odoo.http import request

class PosOrderController(http.Controller):

    @http.route(['/pos/order/receipt_fiscal'], type='json', auth="public", csrf=False)
    def pos_order_receipt_fiscal(self, order_id):
        order = request.env['pos.order'].sudo().browse(order_id)
        return {
            'cae': order.cae,
            'cae_due_date': order.cae_due_date,
            'qr_afip_base64': order.qr_afip_base64,
            'company_cuit': order.company_cuit,
            'pos_branch': order.pos_branch,
            'pos_reference': order.pos_reference,
        }
