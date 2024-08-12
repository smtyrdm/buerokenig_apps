from odoo import api, fields, models, _
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_attribute_category_id = fields.Many2one(
        'product.attribute.category',
        string='Attribute Category'
    )
