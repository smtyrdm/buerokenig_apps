{
    'name': 'Incoterm',
    'version': '15.0',
    'category': '',
    'author': 'Ensa',
    "depends": ['base', 'sale', 'account', 'stock', 'sale_management'],
    'assets': {
        'web.assets_backend': [],
        'web.assets_qweb': [],
    },
    'data': [
        'views/account_incoterms_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'reports/report_saleorder_document.xml',
        'reports/delivery_slip.xml',

    ],
    'license': 'LGPL-3',
    # 'installable': True,
    # 'application': True,
    # 'auto_install': False,
}
