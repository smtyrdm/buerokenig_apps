from odoo import models, fields, api

class ProductAttributeSet(models.Model):
    _name = 'product.attribute.set'
    _description = 'Product Attribute Set'

    name = fields.Char('Name', required=True)
    attribute_line_ids = fields.One2many(
        'product.attribute.set.line', 'attribute_set_id', string='Attributes')

class ProductAttributeSetLine(models.Model):
    _name = 'product.attribute.set.line'
    _description = 'Product Attribute Set Line'

    attribute_set_id = fields.Many2one(
        'product.attribute.set', string='Attribute Set', required=True)
    attribute_id = fields.Many2one(
        'product.attribute', string='Attribute', required=True)
    value_ids = fields.Many2many(
        'product.attribute.value', string='Attribute Values')


    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        if self.attribute_id:
            return {
                'domain': {'value_ids': [('attribute_id', '=', self.attribute_id.id)]}
            }
        else:
            return {'domain': {'value_ids': []}}