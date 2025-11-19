{
    "name": "MezzTT POS Benefits Backend",
    "summary": "Giftcards, Cupones y Puntos para POS",
    "version": "1.0",
    "author": "MezzTT",
    "depends": ["base", "point_of_sale"],
    "category": "Point of Sale",
    "installable": True,
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/giftcard_views.xml",
        "views/coupon_views.xml",
        "views/points_views.xml",
        "views/pos_benefits_menus.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "mezztt_pos_benefits/static/src/js/BenefitsButton.js",
            "mezztt_pos_benefits/static/src/js/BenefitsPopup.js",
            "mezztt_pos_benefits/static/src/xml/BenefitsButton.xml",
            "mezztt_pos_benefits/static/src/xml/BenefitsPopup.xml"
        ]
    }
}
