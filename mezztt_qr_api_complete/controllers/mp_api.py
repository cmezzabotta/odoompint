
import requests
import json
from odoo import http
from odoo.http import request

class MPQRAPIController(http.Controller):

    @http.route('/mpqr/create_order', type='json', auth='public', cors='*')
    def mpqr_create_order(self, amount, order_ref, config_id):
        config = request.env['pos.config'].sudo().browse(config_id)

        token = config.mp_access_token
        store_id = config.mp_store_id
        pos_id = config.mp_pos_id

        url = f"https://api.mercadopago.com/instore/orders/qr/{pos_id}"

        payload = {
            "external_reference": order_ref,
            "title": "POS Kiosk Order",
            "description": "Pago en Totem",
            "amount": amount,
            "store_id": store_id,
            "pos_id": pos_id,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        r = requests.post(url, json=payload, headers=headers)
        return r.json()

    @http.route('/mpqr/check_status', type='json', auth='public', cors='*')
    def mpqr_check_status(self, order_id, config_id):
        config = request.env['pos.config'].sudo().browse(config_id)
        token = config.mp_access_token

        url = f"https://api.mercadopago.com/instore/merchant/orders/{order_id}"
        headers = {"Authorization": f"Bearer {token}"}

        r = requests.get(url, headers=headers)
        return r.json()
