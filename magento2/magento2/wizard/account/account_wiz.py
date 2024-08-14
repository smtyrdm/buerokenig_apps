
import logging

from odoo import models,fields, exceptions, _

_logger = logging.getLogger(__name__)


class AccountFetchWizard(models.Model):
    _name = 'account.fetch.wizard'
    _description = 'Account Fetch Wizard'

    account_fetch_type = fields.Selection([('taxes', 'Fetch Magento Tax'),
                                          ('payment', 'Fetch Magento Payment Method'),
                                          ('incoterm', 'Fetch Magento Incoterm')],
                                         string="Operation Type")

    def fetch_account(self):
        """Fetch products"""
        if self.account_fetch_type == 'taxes':
            self.fetch_taxes()
        elif self.account_fetch_type == 'payment':
            self.fetch_payment()
        elif self.account_fetch_type == 'incoterm':
            self.fetch_incoterm()

    # "code": "DE - USt.", "rate": 19,               : Kunden kaufen vollbesteuerte Artikel	 (Tamamen vergilendirilen öğeler) (Fully taxed items)
    # "code": "DE - reduzierte USt.", "rate": 7,     : Kunden kaufen ermäßigtbesteuerte Artikel (İndirgenmiş vergi kalemleri) (Reduced taxed items)
    # "code": "DE - ohne USt.", "rate": 0,           : Ust.-befreite Unternehmen kaufen voll- und ermäßigtbesteuerte Artikel (KDV'den muaf şirketler tam ve indirimli vergi kalemleri satın alır)
    def fetch_taxes(self):
        url = '/rest/all/V1/taxRates/search?searchCriteria={}'
        type = 'GET'

        magento_taxes = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)

        try:
            items = magento_taxes['items']
            for i in items:
                taxes = self.env['magento.account.taxes'].search([('code', '=', i['code']), ('rate','=',i['rate'])])
                if taxes:
                    continue
                #assert len(taxes) <= 1, f"Multiple records found for code: {i['code']} and rate: {i['rate']}"
                values={
                    'tax_country_id':i['tax_country_id'],
                    'rate':i['rate'],
                    'code':i['code']
                }
                self.env['magento.account.taxes'].sudo().create(values)
        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)

    # https://buerokoenig.ch/rest/V1/carts/57/payment-methods -> 57 orders içinde "quote_id": 57, bölümünden aldım. herahangi bir müşterinde alsan oluyor.
    # store/conf./sale/Payment Methods
    def fetch_payment(self):
        url = '/rest/V1/carts/57/payment-methods' # Burekonig
        #url = '/rest/V1/carts/1755/payment-methods' # keller
        type = 'GET'

        magento_payment = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)

        try:
            items = magento_payment
            for i in items:
                payment = self.env['magento.account.payment'].search([('code', '=', i['code'])])
                if payment:
                    continue
                #assert len(taxes) <= 1, f"Multiple records found for code: {i['code']}"
                values={
                    'code':i['code'],
                    'title':i['title']
                }
                self.env['magento.account.payment'].sudo().create(values)
        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured  def fetch_payment(self): %s") % e)

    # Confi../Sales/Shipping Setting -> bunun tree sine incoterm eklencek.
    def fetch_incoterm(self):
        url = '/rest/V1/directory/countries'
        type = 'GET'

        magento_incoterm = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)

        try:
            items = magento_incoterm
            for i in items:
                incoterm = self.env['magento.account.incoterm'].search([('code', '=', i['id'])])
                if incoterm:
                    continue
                values={
                    'code':i['id'],
                    'local_name':i['full_name_locale'],
                    'english_name':i['full_name_english'],
                }
                self.env['magento.account.incoterm'].sudo().create(values)
        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)