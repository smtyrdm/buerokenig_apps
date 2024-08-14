
import logging
from odoo import models, fields, exceptions, _

logger = logging.getLogger(__name__)


class MagentoCustomerGroup(models.Model):
    _name = 'magento.customer.group'

    group_id = fields.Char(string="Customer Group Id", readonly=True)
    group = fields.Char(string="Customr Group")
    tax_class = fields.Char(string="Tax Class")







