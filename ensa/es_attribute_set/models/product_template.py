from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attribute_set_ids = fields.Many2many(
        'product.attribute.set',
        'product_attribute_set_rel',
        'product_id',
        'attribute_set_id',
        string='Attribute Sets'
    )

    @api.onchange('attribute_set_ids')
    def _onchange_attribute_set_id(self):
        if self.attribute_set_ids:
            existing_attribute_ids = self.attribute_line_ids.mapped('attribute_id.id')
            lines = []
            for attribute_set_id in self.attribute_set_ids:
                for line in attribute_set_id.attribute_line_ids:
                    if line.attribute_id.id not in existing_attribute_ids:
                        lines.append((0, 0, {
                            'attribute_id': line.attribute_id.id,
                            'value_ids': [(6, 0, line.value_ids.ids)]
                        }))
                        existing_attribute_ids.append(line.attribute_id.id)
            self.attribute_line_ids = lines




