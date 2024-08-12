from odoo import api, fields, models, _

class ProductAttributeCategory(models.Model):
    _name = 'product.attribute.category'
    _description = 'Product Attribute Category'

    name = fields.Char(string='Category Name', required=True)
    product_attributes = fields.One2many('product.attribute', 'attribute_category_id', string='Product Attributes')


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    attribute_category_id = fields.Many2one('product.attribute.category', string='Attribute Category', index=True, required=False)
