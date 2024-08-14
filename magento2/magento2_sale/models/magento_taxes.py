
import logging
from odoo import models, fields, exceptions, _, api

logger = logging.getLogger(__name__)

class MagentoTaxes(models.Model):
    _inherit = 'magento.account.taxes'


    def find_magento_catalog_taxes(self, i, line):
        #applied_taxes = i['extension_attributes']['applied_taxes'][0] # magentodan isveç kdv bilgileri gelmiyor.
        # avrupada KDV shipping göre store/conf./sales/tax/Calculation Settings bölümünde "Tax Calculation Based On": Shipping
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_tax_calculation = ICPSudo.get_param('magento2.magento_tax_calculation')
        ship_country = i.get("extension_attributes", {}).get("shipping_assignments", [{}])[0].get("shipping", {}).get("address", {}).get('country_id','')
        bill_country = i.get("billing_address", {}).get('country_id','')
        #country = ship_country if ship_country else bill_country
        if magento_tax_calculation == 'shipping':
            country = ship_country or bill_country # bazen magento hatasından dolayı ship gelmeyebilir.
        elif  magento_tax_calculation == 'billing':
            country = bill_country
        else:
            raise models.ValidationError('Odoo/Setting/Magento/Tax Calculation Based On ?? ')


        tax_percent = line.get('tax_percent', False)
        tax_percent = float(tax_percent) if tax_percent >= 0 else False
        # Engin: Bu sorgu çok mantıklı bu kesinlikle değiştirme
        tax = self.search([('rate','=',tax_percent), ('tax_country_id','=',country)], limit=1)
        if not tax or tax and not tax.tax_id: # tax.tax_id magento models ait 'magento.account.taxes' bunu tree görürüsün
            raise models.ValidationError(f"Account/Magento Taxes | {country} | {tax_percent} not!")
        taxes = tax.tax_id

        return taxes