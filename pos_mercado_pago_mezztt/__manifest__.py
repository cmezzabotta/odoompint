{
    "name": "POS Mercado Pago QR (_mezztt)",
    "summary": "Integra Mercado Pago QR dinámico en el POS de Odoo",
    "version": "16.0.1.0",
    "author": "mezztt",
    "depends": ["point_of_sale", "payment"],
    "data": [
        "data/pos_payment_method_data.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "pos_mercado_pago_mezztt/static/src/app/terminals/mercadopago_qr.js",
            "pos_mercado_pago_mezztt/static/src/app/popups/mp_qr_popup.js",
            "pos_mercado_pago_mezztt/static/src/xml/mp_qr_templates.xml"
        ]
    },
    "installable": True,
    "application": False
}
