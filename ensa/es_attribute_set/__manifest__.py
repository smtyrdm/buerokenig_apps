{
    'name': 'Product Attribute Set',
    'version': '1.0',
    'summary': '',
    'description': '',
    'author': '',
    'depends': ['product','sale','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_attribute_set_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': True,
}
