{
    'name': 'Odoo15 Magento-2.3 Connector',
    'version': '15.0',
    'summary': 'Synchronize data between Odoo and Magento',
    'description': 'Synchronize data between Odoo and Magento, Magento, Magentov15, Magento Odoo, Odoo Magento, Magento Connector',
    'category': 'Extra Tools',
    'author': 'Engin Ülger',
    'depends': ['base', 'sale_management', 'stock', 'account'],
    'website': 'https://cybrosys.com',
    'data': ['security/ir.model.access.csv',
             'data/magento_sequence.xml',
             # Setting
            'views/setting/ir_cron.xml',
            'views/setting/ir_logging.xml',
            'views/setting/res_config_settings.xml',
             # Account
             'views/account/magento_taxes.xml',
             'views/account/magento_payment.xml',
             'views/account/magento_incoterm.xml',
             'wizard/account/account_wiz.xml',
             # Customer
             'views/customer/customer_group_view.xml',
             'wizard/customer/fetch_customer_groups_wiz.xml',
             # Store
             'views/store/magento_website.xml',
             'wizard/store/website_wiz.xml',
             # Products 
             'views/product/magento_product.xml',
             'wizard/product/fetch_products_wiz.xml',
             # menu herzaman en altta tanımlaman gereklidir.
             'views/menu.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'magento2/static/src/css/magento_dashboard.css',
            'magento2/static/src/js/magento_dashboard.js',
            'magento2/static/src/js/lib/Chart.bundle.js',
        ],
        'web.assets_qweb': [
            'magento2/static/src/xml/magento_dashboard.xml',
        ]},
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'price': 49,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
