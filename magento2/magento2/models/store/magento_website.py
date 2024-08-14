
import logging
from odoo import models, fields, exceptions, _, api

logger = logging.getLogger(__name__)


class MagentoWebsite(models.Model):
    _name = 'magento.website'

    name = fields.Char(string="Magento Website", readonly=True,
                       copy=False, default='Draft')

    website_name = fields.Char(string="Website Name")
    website_code = fields.Char(string="Code")
    default_store = fields.Char(string="Default Store")
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'magento.website')
        return super(MagentoWebsite, self).create(vals)


class MagentoStores(models.Model):
    _name = 'magento.stores'

    name = fields.Char(string="Magento Store", readonly=True,
                       copy=False, default='Draft')

    store_id = fields.Char(string="Store ID")
    store_name = fields.Char(string="Store Name")
    store_code = fields.Char(string="Store Code")
    default_website = fields.Char(string="Default Website")
    lang_id = fields.Many2one(comodel_name='res.lang', string='Odoo Language', help="Language Name")

    _sql_constraints = [
        ('store_id_uniq', 'unique(store_id)', 'The code must be unique!'),
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'magento.stores')
        return super(MagentoStores, self).create(vals)




