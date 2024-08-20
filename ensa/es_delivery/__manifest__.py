{
    'name': 'Delivery Date: Week',
    'version': '15.0.1.0.0',
    'category': 'Widget',
    'summery': ' ',
    'author': 'Ensa',
    'website': "",
    "depends": ['base', 'web',"mail", "sale_management", 'purchase'],
    'assets': {
        'web.assets_backend': [
            'es_delivery/static/src/js/dateweek.js',
        ],
        'web.assets_qweb': [],
    },
    'data': [
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_picking_view.xml',
        #'reports/report_saleorder.xml', l10n_din5008_sale
        'reports/report_purchase.xml',
        'reports/report_picking.xml',
        'reports/report_deliveryslip.xml',
        'reports/report_purchasequotation_document.xml',
    ],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
