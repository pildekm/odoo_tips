# -*- coding: utf-8 -*-

{
    "name": """Inventory card""",
    "summary": """Data on inventory card for localization""",
    "category": "Localization / Croatia",
    "images": [],
    "version": "1.0.0",
    "application": False,

    "author": "GMM",
    "support": "",
    "website": "",
    "licence": "LGPL-3",


    "depends": ['account', 'stock'],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": ['view/account_invoice_views.xml',
	         'view/stock_move_views.xml', ],
    "qweb": [],
    "demo": [],


    "auto_install": False,
    "installable": True,
}
