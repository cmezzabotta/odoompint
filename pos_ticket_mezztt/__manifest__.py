
{
    "name": "POS Ticket Mezztt",
    "version": "1.0",
    "summary": "Emisión automática de ticket fiscal",
    "author": "Mezztt",
    "category": "Point of Sale",
    "depends": ["point_of_sale", "l10n_ar_afipws"],
    "data": [],
    "assets": {
        "point_of_sale.assets": [
            "pos_ticket_mezztt/static/src/xml/fiscal_ticket_template.xml",
            "pos_ticket_mezztt/static/src/css/ticket_style.css",
            "pos_ticket_mezztt/static/src/js/fiscal_receipt.js",
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3"
}
