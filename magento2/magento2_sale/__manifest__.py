{
    'name': 'Magento2 Sale',
    'version': '15.0',
    'category': 'Extra Tools',
    'author': 'Engin Ülger',
    'depends': ['base', 'sale_management', 'account', 'magento2', ],
    'data': ['security/ir.model.access.csv',
             'data/magento_data.xml',
             'views/account_move.xml',
             'views/sale_order.xml',
             'views/inherit_orders_view.xml',
             'views/customer.xml',

             'wizard/fetch_orders_wiz.xml',
             'wizard/fetch_customers_wiz.xml',

             'views/menu.xml',
             ],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
