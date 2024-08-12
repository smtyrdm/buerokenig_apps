from odoo import api, fields, models, _

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    attribute_category_id = fields.Many2one('product.attribute.category', string='Attribute Category', index=True, required=False)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attribute_category_id = fields.Many2one('product.attribute.category',string='Attribute Category')

class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    attribute_category_id = fields.Many2one(related='product_tmpl_id.attribute_category_id')

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        attribute = self.env['product.attribute'].search([('attribute_category_id','=',self.attribute_category_id.id)])
        attribute_ids = attribute.ids if attribute else []

        return {'domain': {'attribute_id': [('id', 'in', attribute_ids)]}}

