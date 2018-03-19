

{
    "name": "Manufacturer Certificate",
    "summary": """Manufacturer certificate publishing""",
    "version": "1.0",
	"summary": "Inventory",
    "author": "GMM",
    "license": "GPL-3",
    "category": "Inventory",
    "depends": ['mail', 'contacts', 'website'],
    "data": [
        'security/manufacturer_certificate_security.xml',
        'security/ir.model.access.csv',
        'report/payment_data_report_def.xml',
        'view/report_payment_data.xml',
        'data/manufacture_certificate_mail.xml',
        'view/manufacturer_certificate_view.xml',
        'view/manufacturer_certificate_menus.xml',
        'view/prijava_page.xml',
        'view/web_menus.xml',
    ],
        # 'wizard/upload_certification_document_view.xml',],
    'installable': True,
}
