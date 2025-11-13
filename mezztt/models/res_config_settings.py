# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mp_access_token = fields.Char(
        string="Access Token",
        help="Token privado utilizado para autenticar todas las peticiones contra la API de Mercado Pago."
    )
    mp_public_key = fields.Char(
        string="Public Key",
        help="Clave pública utilizada en integraciones de cliente para inicializar los widgets de Mercado Pago."
    )
    mp_user_id = fields.Char(
        string="User ID",
        help="Identificador del usuario/seller en Mercado Pago. Se utiliza para asociar las órdenes al comercio correcto."
    )
    mp_collector_id = fields.Char(
        string="Collector ID",
        help="Identificador del cobrador asociado al comercio. Necesario para vincular la caja receptora."
    )
    mp_integrator_id = fields.Char(
        string="Integrator ID",
        help="Identificador provisto por Mercado Pago para integradores certificados. Mejora el seguimiento de la app."
    )
    mp_sponsor_id = fields.Char(
        string="Sponsor ID",
        help="Sponsor ID en caso de trabajar con cuentas vinculadas a partners."
    )
    mp_external_store_id = fields.Char(
        string="External Store ID",
        help="Identificador de la sucursal. Debe coincidir con el store_id configurado en Mercado Pago."
    )
    mp_external_pos_id = fields.Char(
        string="External POS ID",
        help="Identificador de la caja o puesto dentro de la sucursal (external_pos_id)."
    )
    mp_pos_id = fields.Char(
        string="POS ID",
        help="Identificador numérico de la caja generado por Mercado Pago (pos_id)."
    )
    mp_qr_mode = fields.Selection(
        selection=[
            ("dynamic", "QR dinámico"),
            ("static", "QR estático"),
        ],
        string="Modo de QR",
        default="dynamic",
        help="Selecciona si se debe generar un código QR dinámico con monto exacto o reutilizar un QR estático."
    )
    mp_notification_url = fields.Char(
        string="URL de notificación",
        help="Endpoint HTTPS público donde Mercado Pago notificará los estados de pago (webhooks)."
    )

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        param_map = {
            'mp_access_token': self.mp_access_token,
            'mp_public_key': self.mp_public_key,
            'mp_user_id': self.mp_user_id,
            'mp_collector_id': self.mp_collector_id,
            'mp_integrator_id': self.mp_integrator_id,
            'mp_sponsor_id': self.mp_sponsor_id,
            'mp_external_store_id': self.mp_external_store_id,
            'mp_external_pos_id': self.mp_external_pos_id,
            'mp_pos_id': self.mp_pos_id,
            'mp_qr_mode': self.mp_qr_mode,
            'mp_notification_url': self.mp_notification_url,
        }
        for key, value in param_map.items():
            params.set_param(f"mezztt.{key}", value or False)

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'mp_access_token': params.get_param('mezztt.mp_access_token'),
            'mp_public_key': params.get_param('mezztt.mp_public_key'),
            'mp_user_id': params.get_param('mezztt.mp_user_id'),
            'mp_collector_id': params.get_param('mezztt.mp_collector_id'),
            'mp_integrator_id': params.get_param('mezztt.mp_integrator_id'),
            'mp_sponsor_id': params.get_param('mezztt.mp_sponsor_id'),
            'mp_external_store_id': params.get_param('mezztt.mp_external_store_id'),
            'mp_external_pos_id': params.get_param('mezztt.mp_external_pos_id'),
            'mp_pos_id': params.get_param('mezztt.mp_pos_id'),
            'mp_qr_mode': params.get_param('mezztt.mp_qr_mode', default='dynamic'),
            'mp_notification_url': params.get_param('mezztt.mp_notification_url'),
        })
        return res

    def action_test_connection(self):
        self.ensure_one()
        client = self.env['mezztt.mercadopago.client']
        try:
            result = client.sudo().test_connection()
        except Exception as exc:  # pragma: no cover - fallback for UI feedback
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Mercado Pago'),
                    'message': _('Error al verificar las credenciales: %s') % (exc,),
                    'sticky': True,
                    'type': 'danger',
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Mercado Pago'),
                'message': _('Conexión verificada correctamente. Identificador: %s') % result,
                'sticky': False,
                'type': 'success',
            },
        }
