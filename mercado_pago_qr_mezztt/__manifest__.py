# -*- coding: utf-8 -*-
{
    "name": "Mercado Pago QR for POS (mezztt)",
    "summary": "Cobro con código QR estático integrado a Mercado Pago para el POS de Odoo 18.",
    "description": """Extiende el Punto de Venta moderno (OWL) para mostrar un popup de pago con código QR estático de Mercado Pago y crear órdenes reales mediante la API oficial.""",
    "version": "18.0.1.0.0",
    "author": "mezztt",
    "website": "https://www.mercadopago.com.ar",
    "license": "LGPL-3",
    "category": "Point of Sale",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/pos_payment_method_data.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "mercado_pago_qr_mezztt/static/src/css/mercado_pago_popup.css",
            "mercado_pago_qr_mezztt/static/src/js/mp_config.js",
            "mercado_pago_qr_mezztt/static/src/js/mercado_pago_popup.js",
            "mercado_pago_qr_mezztt/static/src/js/mercado_pago_terminal.js",
            "mercado_pago_qr_mezztt/static/src/xml/mercado_pago_popup.xml",
        ],
    },
    "installable": True,
    "application": False,
}
