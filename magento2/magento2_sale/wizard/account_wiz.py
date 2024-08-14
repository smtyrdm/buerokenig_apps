from odoo import models, fields, exceptions, _
import logging

_logger = logging.getLogger(__name__)


class AccountFetchWizard(models.Model):
    _inherit = 'account.fetch.wizard'

    def find_magento_service_shipping(self, i, order_line):
        if not i['shipping_amount']:
            return order_line
        product_ship_id = self.env['magento.account.incoterm'].find_magento_incoterm(i, 'shipping')
        taxes = self.__find_shipping_tax_percent(i)
        ship_list = {
            'name': product_ship_id.name,
            'product_id': product_ship_id.id,
            'product_uom_qty': 1,
            'price_unit': i['shipping_amount'],  # bu vergi hariç gelir her zaman
            'tax_id': [(6, 0, [taxes.id])],
        }

        return order_line.append((0, 0, ship_list))

    def __find_shipping_tax_percent(self, i):
        # 1. shipping kendi kdv bilgisi geliyor zaten kdv==0 ise gelmiyor
        for order_res in i.get('extension_attributes', {}).get('item_applied_taxes', []):
            if order_res.get('type') == "shipping" and order_res.get('applied_taxes'):
                for tax in order_res.get('applied_taxes', list()):
                    percent = tax.get('percent', False)
                    percent = float(percent) if percent >= 0 else False
                    taxes = self.env['magento.account.taxes'].find_magento_catalog_taxes(i, {'tax_percent': percent})
                    return taxes
        # 2. shipping_amount her zaman kdv hariç gelir, shipping_incl_tax her zaman kdv dahil gelir.
        shipping_amount = i.get('shipping_amount', 0)
        shipping_incl_tax = i.get('shipping_incl_tax', 0)
        if shipping_amount == shipping_incl_tax:
            taxes = self.env['magento.account.taxes'].find_magento_catalog_taxes(i, {'tax_percent': 0.0})
            return taxes
        else:
            ship_percent = float((shipping_incl_tax / shipping_amount - 1) * 100)
            taxes = self.env['magento.account.taxes'].find_magento_catalog_taxes(i, {'tax_percent': round(ship_percent,1)})
            return taxes

        raise models.ValidationError(f"{shipping_amount} shipping kdv bilgiside gelmiyor")

    def find_magento_service_discount(self, i, order_line):
        i['discount_excl_tax'] = 0
        if not i['discount_amount']:
            return order_line
        product_disc_id = self.env['magento.account.incoterm'].find_magento_incoterm(i, 'discount')
        taxes, disc_amount = self.__find_discount_tax_percent(i)
        disc_list = {
            'name': product_disc_id.name,
            'product_id': product_disc_id.id,
            'product_uom_qty': 1,
            'price_unit': disc_amount,  # burası çok karışık
            'tax_id': [(6, 0, [taxes.id])],
        }
        return order_line.append((0, 0, disc_list))


    def __find_discount_tax_percent(self, i):
        tax_percents = [line["tax_percent"] for line in i['items']]
        max_percent = float(max(tax_percents))
        taxes = self.env['magento.account.taxes'].find_magento_catalog_taxes(i, {'tax_percent': max_percent})
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_tax_discount_price = ICPSudo.get_param('magento2.magento_tax_discount_price')
        if magento_tax_discount_price == 'excluding_tax': # vergi hariç
            i['discount_excl_tax'] = i['discount_amount']
            return taxes, i['discount_amount']
        if magento_tax_discount_price == 'including_tax': # vergi dahil
            discount_amount = i['discount_amount'] / (1 + (max_percent / 100))
            i['discount_excl_tax'] = discount_amount
            return taxes, discount_amount

        raise models.ValidationError(f"Discount Amount kdv hesaplanamadı..... :) ")



    # # İlk elemanın tax_percent değerini alıyoruz
    # first_tax_percent = i['items'][0]["tax_percent"]
    # # Tüm elemanların tax_percent değerlerini kontrol ediyoruz. Aynı ise ship percent de aynıdır.
    # all_same = all(line["tax_percent"] == first_tax_percent for line in i['items'])
    # ship_tax = OdooTaxes.search([('rate', '=', first_tax_percent), ('tax_country_id', '=', country_code)], limit=1)
    # if ship_tax and all_same:
    #     return ship_tax

    # ship_tax = self.__find_shipping_tax_percent(i, country_code)
    # ship_tax_type = self.__find_tax_type(i.get('extension_attributes'), 'apply_shipping_on_prices')
    # incl_amount = i.get('shipping_incl_tax', 0.0)  # True : including_tax
    # excl_amount = i.get('shipping_amount', 0.0)  # False: excluding_tax
    # ship_amount = incl_amount if ship_tax_type else excl_amount

    # 3. son ihtimal
    # if not ship_tax:
    #     ship_tax = OdooTaxes.search([('rate', '=', 0.0), ('tax_country_id', '=', country_code)], limit=1)
    #     if ship_tax:
    #         return ship_tax
