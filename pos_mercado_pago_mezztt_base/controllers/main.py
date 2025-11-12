from odoo import http
from odoo.http import request

class MercadoPagoMezzttController(http.Controller):
    @http.route("/mp/mezztt/test", auth="public", type="http")
    def test(self):
        return "Modulo POS Mercado Pago _mezztt base instalado correctamente"
