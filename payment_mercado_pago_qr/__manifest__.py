{
    'name': 'Mercado Pago QR Payments',
    'version': '1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Accept Mercado Pago QR code payments during checkout',
    'author': 'Pronexo / Mezztt',
    'website': 'https://www.pronexo.com',
    'license': 'LGPL-3',
    'depends': ['payment', 'website_sale'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_mercado_pago_qr/static/src/js/mercado_pago_qr_payment.js',
        ],
    },
    'installable': True,
}
