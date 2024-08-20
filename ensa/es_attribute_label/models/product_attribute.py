from odoo import api, models, fields, _

class ProductAttributeLabel(models.Model):
    _name = 'product.attribute.label'
    _description = 'Product Attribute Label'

    name = fields.Char("Label Name", required=True)
    attribute_id = fields.Many2one('product.attribute', string="Attribute", required=True, ondelete='cascade')


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    label_ids = fields.One2many('product.attribute.label', 'attribute_id', string="Labels", domain="[('attribute_id', '=', active_id)]")

class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    label_id = fields.Many2one('product.attribute.label', string="Label", domain="[('attribute_id', '=', attribute_id)]")

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        self.label_id = False  # Attribute değiştiğinde label alanını sıfırla
        return {'domain': {'label_id': [('attribute_id', '=', self.attribute_id.id)]}}

