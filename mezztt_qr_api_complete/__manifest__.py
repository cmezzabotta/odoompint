{
    "name": "Mezztt POS Mercado Pago QR Estático",
    "version": "18.0.1.0.0",
    "author": "Mezztt",
    "category": "Point of Sale",
    "license": "LGPL-3",
    "summary": "Terminal Mercado Pago QR estático para el POS estándar",
    "depends": ["point_of_sale"],
    "data": [
        "data/pos_payment_terminal_data.xml",
        "views/pos_payment_method_views.xml",
        "security/ir.model.access.csv"
    ],
    "assets": {
        "point_of_sale.assets": [
            "mezztt_qr_api_complete/static/src/app/services/pos_store_patch.js",
            "mezztt_qr_api_complete/static/src/app/components/mp_qr_popup/mp_qr_popup.js",
            "mezztt_qr_api_complete/static/src/app/components/mp_qr_popup/mp_qr_popup.xml",
            "mezztt_qr_api_complete/static/src/app/utils/payment/payment_mp_qr_static.js",
        ]
    },
    "installable": True,
}
