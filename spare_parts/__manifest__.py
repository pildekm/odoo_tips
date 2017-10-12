{
    'name' : 'Spare Parts',
    'version' : '1.0.1',
    'author' : 'M&G sin_vetra',
    'license': 'GPL-3',
    'category' : 'Sale',
    'website' : '/',
    'depends' : ['product','product_brand','stock','purchase','website_sale'],
    'data':[
        'view/spare_parts_view.xml',
        #'view/res_config.xml',
        'view/sale_order_view.xml',
        'wizard/sale_order_stock_quantity_view.xml',
        ],
    'installable': True
}
