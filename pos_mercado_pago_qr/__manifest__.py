{
    'name': 'POS Mercado Pago QR',
    'summary': 'Dynamic QR payments with Mercado Pago in the POS',
    'version': '16.0.1.0.0',
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
        'point_of_sale._assets_pos': [
            'pos_mercado_pago_qr/static/src/**/*',
        ],
    },
    'images': ['static/description/icon.svg'],
    'installable': True,
    'application': False,
}
