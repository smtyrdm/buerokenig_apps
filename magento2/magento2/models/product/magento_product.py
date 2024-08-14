from odoo import models, fields, api

class MagentoProduct(models.Model):
    _name = 'magento.product'
    _description = 'Magento Product'

    sku = fields.Char(string="Product SKU", required=True)
    name = fields.Char(string="Product Name", translate=True)
    price = fields.Float(string="Product Price")
    status = fields.Selection([('1', 'Enabled'), ('2', 'Disabled')], string="Product Status")
    type = fields.Char(string="Product Type")
    visibility = fields.Selection([
        ('1', 'Not Visible Individually'),
        ('2', 'Catalog'),
        ('3', 'Search'),
        ('4', 'Catalog, Search')
    ], string="Product Visibility")
    magento_store_id = fields.Many2one(comodel_name='magento.stores', string="Magento Store")

    _sql_constraints = [
        ('sku_uniq', 'unique(sku)', 'The SKU must be unique!'),
    ]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    magento = fields.Boolean(string="Magento")
    magento_product_id = fields.Many2one('magento.product', string="Magento Product")



