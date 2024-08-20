# -*- coding: utf-8 -*-
{
    'name': 'Dynamic Sales Terms and Condition',
    'version': '15.0',
    'category': 'Facility',
    'license': 'OPL-1',
    'images': ['static/description/sale002.png'],
    'author': 'oranga, Engin Ülger',
    'summary': 'Sales Terms, Conditions, Agreements, Contracts in Quotation and Sale order',
    'description': """
    Warranty List
    Sales Warranty Cards
    Warranty Template
    Design Sales agreements
    Agreements sales
""",
    # web_domain_field -> modülü domain=field yazmamıza yarıyor.
    # om_account_accountant bunu kaldırdım, neden eklemişim bilmiyorum.
    'depends': ['base','web', 'mail', 'sale', 'account','stock', 'purchase', 'web_domain_field'],
    'data': [
        'views/term_condition.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'security/ir.model.access.csv',
        'report/sale_order_report.xml',
        'report/account_move_report.xml',
        'report/purchase_order_report.xml',
        'report/stock_picking_report.xml',
        'views/menu.xml', # menu herzaman en altta
    ],
    'installable': True,
    'application': True,
}