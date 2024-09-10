from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    magento = fields.Boolean(string="Magento")
    magento_url_key =  fields.Char(string="Magento URL") # frond url giriş
    magento_product_id = fields.Char(string="Magento Product") # admin paneline giriş

    magento_sku = fields.Char(string="Magento SKU") # magento ana SKU göre API istekleri yapılması.


    def action_magento_product_admin(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_admin_url = ICPSudo.get_param('magento2.magento_admin_url')
        url = f"https://{magento_admin_url}/catalog/product/edit/id/{self.magento_product_id}/"
        if magento_admin_url and self.magento_product_id:
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',  # Opens in a new tab
            }
    def action_magento_product_store(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_host = ICPSudo.get_param('magento2.magento_host')
        url = f"https://{magento_host}/{self.magento_url_key}/"
        if magento_host and self.magento_url_key:
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',  # Opens in a new tab
            }


# class ProductCategory(models.Model):
#     _inherit = 'product.category'
#
#     magento_name = fields.Char(string="Magento Name")
#     magento_id = fields.Char(string="Magento ID")