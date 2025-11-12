{
    'name': 'POS Mercado Pago QR (_mezztt)',
    'summary': 'Dynamic QR payments with Mercado Pago for the POS',
    'version': '16.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'author': 'Mezztt',
    'license': 'LGPL-3',
    'website': 'https://www.mercadopago.com.ar',
    'depends': ['point_of_sale', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_mercado_pago_mezztt/static/src/js/mercado_pago_terminal.js',
            'pos_mercado_pago_mezztt/static/src/xml/mercado_pago_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
}
