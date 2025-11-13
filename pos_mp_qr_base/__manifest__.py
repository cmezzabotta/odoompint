
{
    "name": "POS MercadoPago QR Base",
    "summary": "Base visual para integración QR MercadoPago en POS",
    "version": "1.0",
    "category": "Point of Sale",
    "author": "Heladería Autoservicio",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/pos_payment_method_view.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "/pos_mp_qr_base/static/src/js/qr_popup.js",
            "/pos_mp_qr_base/static/src/xml/qr_popup.xml",
            "/pos_mp_qr_base/static/src/xml/pos_receipt.xml",
            "/pos_mp_qr_base/static/src/css/qr_popup.css",
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False
}
