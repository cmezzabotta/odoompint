{
    "name": "POS Mercado Pago QR (_mezztt) Base",
    "summary": "Base del módulo POS para integración con Mercado Pago QR",
    "version": "16.0.0.1",
    "author": "mezztt",
    "depends": ["point_of_sale", "payment"],
    "data": [
        "data/pos_payment_method_data.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "pos_mercado_pago_mezztt_base/static/src/app/terminals/mercadopago_qr.js",
            "pos_mercado_pago_mezztt_base/static/src/app/popups/mp_qr_popup.js",
            "pos_mercado_pago_mezztt_base/static/src/xml/mp_qr_templates.xml"
        ]
    },
    "installable": True,
    "application": False
}
