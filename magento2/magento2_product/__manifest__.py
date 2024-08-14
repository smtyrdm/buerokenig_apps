{
    'name': 'Magento2 Product',
    'version': '15.0',
    'category': 'Extra Tools',
    'author': '',
    'depends': ['base', 'sale_management', 'account', 'magento2'],
    'data': ['security/ir.model.access.csv',
             # Products
             'views/magento_product.xml',
             'wizard/fetch_products_wiz.xml',
             'views/menu.xml',
             ],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
