from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        params = super()._loader_params_pos_payment_method()
        extra_fields = [
            'mpqr_use_qr',
            'mpqr_collector_id',
            'mpqr_pos_external_id',
            'mpqr_store_id',
            'mpqr_order_validity',
            'mpqr_receipt_message',
        ]
        params['search_params']['fields'].extend(f for f in extra_fields if f not in params['search_params']['fields'])
        return params
