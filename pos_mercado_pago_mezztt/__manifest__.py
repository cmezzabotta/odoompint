{
    "name": "POS Mercado Pago QR (_mezztt)",
    "summary": "Terminal virtual Mercado Pago QR para POS (QR dinámico in-POS).",
    "version": "16.0.1.0.0",
    "author": "mezztt",
    "depends": ["point_of_sale", "payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml"
    ],
    "assets": {
        "point_of_sale.assets": [
            "pos_mercado_pago_mezztt/static/src/app/terminals/mercadopago_qr.js",
            "pos_mercado_pago_mezztt/static/src/app/popups/mp_qr_popup.js",
            "pos_mercado_pago_mezztt/static/src/xml/mp_qr_templates.xml"
        ]
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False
}
