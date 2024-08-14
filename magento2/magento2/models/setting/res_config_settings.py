import logging
import json
from odoo import models, fields, api, exceptions, _
logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.info("Unable to import requests, please install it with pip install requests")

# magento2/store/magento_connection.py
class MagentoConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    access_token = fields.Char(string="Access Token")
    magento_host = fields.Char(string="Magento Host")
    magento_admin_url = fields.Char(string="Admin Panel")

    magento_tax_catalog_price = fields.Selection([('excluding_tax', 'Excluding Tax'), ('including_tax', 'Including Tax')],  string="Catalog Prices")
    magento_tax_shipping_price = fields.Selection([('excluding_tax', 'Excluding Tax'), ('including_tax', 'Including Tax')], string="Shipping Prices")
    magento_tax_discount_price = fields.Selection([('excluding_tax', 'Excluding Tax'), ('including_tax', 'Including Tax')], string="Discount Prices")
    # Store/Conf/Sales/Tax/ Calculation Settings
    # Bu ayar müşteri adresine göre KDV(taxes) belirliyor.
    # fatura adresi CH fakat teslim adresi DE, kdv shipping göre ise:19% (DE) | kdv billing göre ise:0% (CH) misal
    magento_tax_calculation = fields.Selection([
        ('shipping', 'Shipping Address'),
        ('billing', 'Billing Address'),
    ], string='Tax Calculation Based On')

    @api.model
    def get_values(self):
        res = super(MagentoConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        access_token = ICPSudo.get_param('magento2.access_token')
        magento_host = ICPSudo.get_param('magento2.magento_host')
        # Tax Calculator
        magento_tax_catalog_price = ICPSudo.get_param('magento2.magento_tax_catalog_price')
        magento_tax_shipping_price = ICPSudo.get_param('magento2.magento_tax_shipping_price')
        magento_tax_discount_price = ICPSudo.get_param('magento2.magento_tax_discount_price')
        magento_tax_calculation = ICPSudo.get_param('magento2.magento_tax_calculation')
        magento_admin_url = ICPSudo.get_param('magento2.magento_admin_url')

        res.update(
            access_token=access_token,
            magento_host=magento_host,
            magento_tax_catalog_price=magento_tax_catalog_price,
            magento_tax_shipping_price=magento_tax_shipping_price,
            magento_tax_discount_price=magento_tax_discount_price,
            magento_tax_calculation=magento_tax_calculation,
            magento_admin_url=magento_admin_url,
        )
        return res

    def set_values(self):
        super(MagentoConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("magento2.access_token", self.access_token)
        ICPSudo.set_param("magento2.magento_host", self.magento_host)
        ICPSudo.set_param("magento2.magento_tax_catalog_price", self.magento_tax_catalog_price)
        ICPSudo.set_param("magento2.magento_tax_shipping_price", self.magento_tax_shipping_price)
        ICPSudo.set_param("magento2.magento_tax_discount_price", self.magento_tax_discount_price)
        ICPSudo.set_param("magento2.magento_tax_calculation", self.magento_tax_calculation)
        ICPSudo.set_param("magento2.magento_admin_url", self.magento_admin_url)

