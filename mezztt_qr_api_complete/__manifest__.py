
{
    "name": "Mezztt POS Mercado Pago QR (Totem)",
    "version": "1.0",
    "author": "Mezztt",
    "category": "Point of Sale",
    "license": "LGPL-3",
    "summary": "Mercado Pago QR",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_config_view.xml",
        "views/payment_method_view.xml",
        "views/assets.xml",
        "security/ir.model.access.csv"
    ],
    "assets": {
        "point_of_sale.assets": [
            "mezztt_qr_api_complete/static/src/js/mp_qr_payment.js",
            "mezztt_qr_api_complete/static/src/xml/mp_qr_templates.xml"
        ]
    },
    "installable": True
}
