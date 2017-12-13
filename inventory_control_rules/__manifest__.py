# -*- coding: utf-8 -*-

{
    "name": """Minimum quantity rules""",
    "summary": """Minimum quantity rule for product in season and off season""",
    "category": "Localization / Croatia",
    "images": [],
    "version": "1.0.0",
    "application": False,

    "author": "GMM",
    "support": "",
    "website": "",
    "licence": "LGPL-3",


    "depends": ['stock'],
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    "data": ['data/season_min_qty_rule.xml',
	         'view/stock_warehouse_views.xml', ],
    "qweb": [],
    "demo": [],


    "auto_install": False,
    "installable": True,
}
