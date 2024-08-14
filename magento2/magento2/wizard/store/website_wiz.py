
import logging

from odoo import models,fields, exceptions, _

_logger = logging.getLogger(__name__)


class WebsiteFetchWizard(models.Model):
    _name = 'website.fetch.wizard'
    _description = 'Website Fetch Wizard'

    website_fetch_type = fields.Selection([('website', 'Fetch magento websites'),
                                          ('stores', 'Fetch Magento stores')],
                                         string="Operation Type")

    def fetch_website(self):
        """Fetch products"""
        if self.website_fetch_type == 'website':
            self.fetch_websites()

        elif self.website_fetch_type == 'stores':
            self.fetch_stores()

    def fetch_websites(self):
        url = '/rest/V1/store/websites'
        type = 'GET'
        magento_websites = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
        try:
            items = magento_websites
            for i in items:
                values={
                    'website_name':i['name'],
                    'website_code':i['code'],
                    'default_store':i['default_group_id']
                }
                print("values", values)
                self.env['magento.website'].sudo().create(values)




        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)

    def fetch_stores(self):
        #url = '/rest/default/V1/store/storeViews'
        url = '/rest/V1/store/storeViews' # de ve fr mağaza sahip
        type = 'GET'
        magento_stores = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
        try:
            items = magento_stores
            for i in items:
                stores = self.env['magento.stores'].search([('store_id', '=', i['id'])])
                values = {
                    'store_id': i['id'],
                    'store_name': i['name'],
                    'store_code': i['code'],
                    'default_website': i['website_id']
                }
                if stores:
                    self.env['magento.stores'].sudo().write(values)
                else:
                    self.env['magento.stores'].sudo().create(values)

        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)