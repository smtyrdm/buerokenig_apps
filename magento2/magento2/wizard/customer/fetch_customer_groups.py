
import logging

from odoo import models, exceptions, _

_logger = logging.getLogger(__name__)


class CustomerGroupFetchWizard(models.Model):
    _name = 'magento_customer_group.fetch.wizard'
    #_inherit = 'order.fetch.wizard'
    _description = 'Customer Group Fetch Wizard'

    def fetch_customer_group(self):
        PartnerObj = self.env['res.partner']
        cr = self._cr
        url = '/rest/V1/customerGroups/search?searchCriteria=0'
        type = 'GET'
        customer_group = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
        try:
            items = customer_group['items']

            cr.execute("select group_id from magento_customer_group "
                       )
            g_id = cr.fetchall()
            g_ids = [i[0] for i in g_id] if g_id else []
            for i in items:
                if g_ids !=[]:
                    _logger.info("ALL IMPORTED")
                else:
                    values = {
                        'group_id': i['id'],
                        'group': i['code'],
                        'tax_class': i['tax_class_name']
                    }
                    self.env['magento.customer.group'].sudo().create(values)

        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)

