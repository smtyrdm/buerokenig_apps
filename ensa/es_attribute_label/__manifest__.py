{
    'name': 'Product Attribute Label',
    'version': '1.0',
    'summary': '',
    'description': '',
    'author': '',
    'depends': ['product','sale','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_attribute_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'application': True,
}
