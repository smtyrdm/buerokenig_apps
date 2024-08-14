
import logging
import json
from odoo import models, fields, api, exceptions, _
logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.info("Unable to import requests, please install it with pip install requests")


class MagentoConnect(models.Model):
    _name = 'magento.connector'
    _description = 'Magento Connector'

    def magento_api_call(self, **kwargs):
        """
        We will be running the api calls from here
        :param kwargs: dictionary with all the necessary parameters,
        such as url, header, data,request type, etc
        :return: response obtained for the api call
        """
        if not kwargs:
            # no arguments passed
            return

        ICPSudo = self.env['ir.config_parameter'].sudo()
        # fetching access token from settings
        try:
            access_token = ICPSudo.get_param('magento2.access_token')
        except:
            access_token = False
            pass
        # fetching host name
        try:
            magento_host = ICPSudo.get_param('magento2.magento_host')
        except:
            magento_host = False
            pass

        try:
            magento_tax_calculation = ICPSudo.get_param('magento2.magento_tax_calculation')
            magento_tax_discount_price = ICPSudo.get_param('magento2.magento_tax_discount_price')

        except:
            magento_tax_calculation = False
            magento_tax_discount_price = False
            pass
        if not access_token or not magento_host or not magento_tax_calculation or not magento_tax_discount_price:
            raise exceptions.UserError(_('Please check the magento configurations!'))
            return

        type = kwargs.get('type') or 'GET'

        complete_url = 'http://'+magento_host+kwargs.get('url')
        print("complete", complete_url)
        logger.info("%s", complete_url)
        headers = kwargs.get('headers')
        headers['Authorization'] = 'Bearer ' + access_token

        data = json.dumps(kwargs.get('data')) if kwargs.get('data') else None
        try:
            res = requests.request(type, complete_url, headers=headers, data=data)
            print(res)
            items = json.loads(res.text)
            print('items', items)

            return items
        except Exception as e:
            logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured 5 %s") %e)
        return
