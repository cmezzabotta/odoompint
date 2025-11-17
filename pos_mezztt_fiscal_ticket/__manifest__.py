{
    'name': 'POS Fiscal Ticket (Mezztt)',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Fiscal ticket printing with AFIP data and automatic invoicing.',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'l10n_ar_afipws_fe'],
    'data': [
        'views/report_invoice_fiscal.xml',
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pos_mezztt_fiscal_ticket/static/src/css/fiscal_ticket.css',
        ],
    },
    'installable': True,
    'application': False,
}
