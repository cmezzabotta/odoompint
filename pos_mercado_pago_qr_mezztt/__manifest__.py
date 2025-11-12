{
    'name': 'POS Mercado Pago QR Mezztt',
    'summary': 'Dynamic QR payments with Mercado Pago in the POS',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'author': 'Mezztt',
    'website': 'https://www.mercadopago.com.ar',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'pos_online_payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_mercado_pago_qr_mezztt/static/src/js/mp_qr_terminal.js',
            'pos_mercado_pago_qr_mezztt/static/src/app/services/pos_store_patch.js',
            'pos_mercado_pago_qr_mezztt/static/src/app/utils/payment/payment_mercado_pago_qr.js',
            'pos_mercado_pago_qr_mezztt/static/src/app/components/popups/mercado_pago_qr_popup/mercado_pago_qr_popup.js',
            'pos_mercado_pago_qr_mezztt/static/src/app/components/popups/mercado_pago_qr_popup/mercado_pago_qr_popup.scss',
        ],
        'point_of_sale.assets_qweb': [
            'pos_mercado_pago_qr_mezztt/static/src/app/components/popups/mercado_pago_qr_popup/mercado_pago_qr_popup.xml',
        ],
    },
    'images': ['static/description/icon.svg'],
    'installable': True,
    'application': True,
}
