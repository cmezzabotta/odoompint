# -*- coding: utf-8 -*-
{
    "name": "Mezztt Mercado Pago QR POS",
    "summary": "Pago con QR dinámico de Mercado Pago para el Punto de Venta",
    "description": """
        Permite configurar todas las credenciales requeridas por Mercado Pago y operar
        con QR dinámico desde el Punto de Venta de Odoo 18. Al pagar con el método
        "Mercado Pago QR" se muestra un checkout moderno que genera el código QR,
        supervisa el pago y finaliza la orden automáticamente al confirmarse.
    """,
    "version": "1.0.0",
    "author": "Mezztt",
    "website": "https://mezztt.com",
    "category": "Point of Sale",
    "license": "LGPL-3",
    "depends": [
        "point_of_sale",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/pos_payment_method_view.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "mezztt_mp_qr/static/src/css/mp_qr_styles.css",
            "mezztt_mp_qr/static/src/xml/mp_qr_templates.xml",
            "mezztt_mp_qr/static/src/js/mp_pos_models.js",
            "mezztt_mp_qr/static/src/js/mp_qr_popup.js",
            "mezztt_mp_qr/static/src/js/mp_payment_screen.js",
        ],
    },
    "installable": True,
    "application": False,
}
