from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_variant_count = fields.Integer(
        '# Product Variants', compute='_compute_product_variant_count')

    @api.depends('product_variant_ids.product_tmpl_id')
    def _compute_product_variant_count(self):
        for template in self:
            template.product_variant_count = len(template.product_variant_ids[0:2])