{
    'name': '(SO PO IN) Tracking',
    'version': '15.0',
    'category': 'Sales',
    'author': 'enginulger06@gmail.com',
    # payment_status -> cybrosys/payment_status_in_sale -> fatura ödeme status geliyor.
    "depends": ["base", "sale", "sale_management", "account","stock", "payment_status_in_sale"],
    'data': [
        'views/sale_order_tree.xml',
        'views/sale_order_form.xml',
        'views/account_move.xml',
    ],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
