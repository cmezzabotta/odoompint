# ticket_mod_pos/__manifest__.py
{
    "name": "Ticket POS - Factura 80mm",
    "summary": "Impresión de facturas del Punto de Venta en ticket térmico de 80 mm",
    "version": "18.0.1.0.0",
    "category": "Accounting/Reporting",
    "author": "Sabores 1972 SA",
    "license": "LGPL-3",
    "depends": ["account", "point_of_sale"],
    "data": [
        "report/templates.xml",
        "report/report.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
