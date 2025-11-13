# -*- coding: utf-8 -*-
from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    mp_qr_enabled = fields.Boolean(
        string='Mercado Pago QR',
        help='Activa el flujo de QR dinámico de Mercado Pago para este método.',
    )
    mp_use_global_credentials = fields.Boolean(
        string='Usar credenciales globales',
        default=True,
        help=(
            'Cuando está marcado se utilizan los datos cargados en Ajustes > Punto de Venta. '
            'Si se desmarca se deben completar manualmente las credenciales para esta caja.'
        ),
    )
    mp_access_token = fields.Char(
        string='Access Token',
        groups='base.group_system',
        help='Token privado provisto por Mercado Pago para autenticar las peticiones.',
    )
    mp_public_key = fields.Char(
        string='Public Key',
        help='Clave pública asociada a la cuenta, útil para integraciones lado cliente.',
    )
    mp_user_id = fields.Char(
        string='User ID',
        help='Identificador del vendedor (user_id) necesario para relacionar la sucursal.',
    )
    mp_collector_id = fields.Char(
        string='Collector ID',
        help='Identificador del cobrador asociado a la cuenta.',
    )
    mp_integrator_id = fields.Char(
        string='Integrator ID',
        help='Identificador otorgado por Mercado Pago a partners e integradores.',
    )
    mp_sponsor_id = fields.Char(
        string='Sponsor ID',
        help='Sponsor ID utilizado cuando la cuenta pertenece a un partner.',
    )
    mp_external_store_id = fields.Char(
        string='External Store ID',
        help='Identificador externo de la sucursal configurado en Mercado Pago.',
    )
    mp_external_pos_id = fields.Char(
        string='External POS ID',
        help='Identificador externo de la caja dentro de la sucursal.',
    )
    mp_pos_id = fields.Char(
        string='POS ID',
        help='Identificador numérico interno (pos_id) provisto por Mercado Pago.',
    )
    mp_notification_url = fields.Char(
        string='URL de notificación',
        help='Webhook HTTPS donde Mercado Pago enviará las notificaciones de pago.',
    )
    mp_qr_mode = fields.Selection(
        [('dynamic', 'QR dinámico'), ('static', 'QR estático')],
        string='Modo de QR',
        default='dynamic',
        help='Define si se genera un QR con importe exacto (dinámico) o reutilizable (estático).',
    )

    def _mp_credentials(self, defaults=None):
        self.ensure_one()
        defaults = defaults or {}
        params = self.env['ir.config_parameter'].sudo()

        def _default(key):
            if defaults.get(key):
                return defaults.get(key)
            return params.get_param(f'mezztt_mp_qr.{key}')

        def _value(field_name, key):
            value = self[field_name]
            if value:
                return value
            if self.mp_use_global_credentials:
                return _default(key)
            return False

        return {
            'access_token': _value('mp_access_token', 'mp_access_token'),
            'public_key': _value('mp_public_key', 'mp_public_key'),
            'user_id': _value('mp_user_id', 'mp_user_id'),
            'collector_id': _value('mp_collector_id', 'mp_collector_id'),
            'integrator_id': _value('mp_integrator_id', 'mp_integrator_id'),
            'sponsor_id': _value('mp_sponsor_id', 'mp_sponsor_id'),
            'external_store_id': _value('mp_external_store_id', 'mp_external_store_id'),
            'external_pos_id': _value('mp_external_pos_id', 'mp_external_pos_id'),
            'pos_id': _value('mp_pos_id', 'mp_pos_id'),
            'qr_mode': _value('mp_qr_mode', 'mp_qr_mode') or 'dynamic',
            'notification_url': _value('mp_notification_url', 'mp_notification_url'),
        }

    def _get_available_payment_method_ids(self):
        return self.filtered('mp_qr_enabled').ids
