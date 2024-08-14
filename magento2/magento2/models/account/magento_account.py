
import logging
from odoo import models, fields, exceptions, _, api

logger = logging.getLogger(__name__)

class MagentoTaxes(models.Model):
    _name = 'magento.account.taxes'

    tax_country_id = fields.Char(string="Country")
    rate = fields.Float(string="Rate")
    code = fields.Char(string="Code")

    tax_id = fields.Many2one('account.tax', string="Odoo Taxes")


    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code must be unique!'),
    ]


# https://buerokoenig.ch/rest/V1/carts/57/payment-methods -> 57 orders içinde "quote_id": 57, bölümünden aldım. herahangi bir müşterinde alsan oluyor.
# https://tableroyale.fr/rest/V1/carts/1/payment-methods -> 1 orders içinde "quote_id": 1,
class MagentoPayment(models.Model):
    _name = 'magento.account.payment'

    code = fields.Char(string="Code")
    title = fields.Char(string="Title")
    payment_term_id = fields.Many2one('account.payment.term', 'Odoo Payment Terms')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code must be unique!'),
    ]


class MagentoIncoterm(models.Model):
    _name = 'magento.account.incoterm'

    code = fields.Char(string="Code")
    local_name = fields.Char(string="Local Name")
    english_name = fields.Char(string="English Name")
    incoterm_id = fields.Many2one('account.incoterms', 'Odoo Incoterm')
    # shipp ülkesi göre discout (indirim) veya shipping (kargo) product service eklenbilir.
    product_disc_id = fields.Many2one('product.product', 'Odoo Product Discount', domain=[('detailed_type','=','service')])
    product_ship_id = fields.Many2one('product.product', 'Odoo Product Shipping', domain=[('detailed_type','=','service')])

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code must be unique!'),
    ]