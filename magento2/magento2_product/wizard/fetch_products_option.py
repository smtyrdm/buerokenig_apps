import logging

from odoo import models, fields, exceptions, _
import urllib.parse
import base64
import requests
import json

_logger = logging.getLogger(__name__)


class ProductFetchWizard(models.Model):
    _inherit = 'product.fetch.wizard'

    product_type = fields.Selection(
        selection_add=[('product_option_price_update', 'Product Option Price Update')]  # Yeni seçenek ekleme
    )


    def fetch_products(self):
        # Orijinal işlevi genişletme
        super(ProductFetchWizard, self).fetch_products()
        if self.product_type == 'product_option_price_update':
            self.fetch_product_option()

    def fetch_product_option(self, item=False):
        # products = self.env['product.template'].search([('magento', '=', True), ('variant_code', '=', 'SSP-EUROT-2-SZ')])
        if item:
            products = self.env['product.template'].search([('magento', '=', True), ('magento_sku', '=', item.magento_sku)])
        else:
            products = self.env['product.template'].search([('magento', '=', True)])
        for product in products:
            sku = urllib.parse.quote(product.magento_sku)
            url = f'/rest/all/V1/products/{sku}'
            prod_option = self._magento_api_call(url)
            if not prod_option:
                continue

            product_type = prod_option.get('type_id')

            # conf_skus alanı için verileri hazırlayın
            conf_skus = False
            if product_type == 'configurable':
                # confs = prod_option.get('extension_attributes', {}).get('configurable_product_options',[])
                # for conf in confs:
                #     attribute_id = conf.get('attribute_id')
                #     self.configurable_product_options(attribute_id)
                conf_skus = self.conf_product_price(sku)

            options = prod_option.get('options', [])

            if conf_skus:
                options.insert(0, {
                    'title': 'CONFS',  # TODO title eklenecek
                    'values': conf_skus
                })

            try:
                json_data = json.dumps(options)
                product.magento_json_data = json_data
            except (TypeError, ValueError) as e:
                raise ValueError(f"JSON formatında hata: {e}")

    def configurable_product_options(self, attribute_id):
        # url içerisindeki all verisi ile sku'lar alınıyor. Eğer "all" yerine store code gönderilirse dile göre çevirileri geliyor.
        url = f'/rest/all/V1/products/attributes/{attribute_id}'
        # url = f'/rest/de/V1/products/attributes/{attribute_id}'
        # url = f'/rest/fr/V1/products/attributes/{attribute_id}'
        json_data = self._magento_api_call(url) or []
        options = json_data.get('options', [])
        _logger.warning('Options %s', options)



    def conf_product_price(self, sku):
        url = f'/rest/V1/configurable-products/{sku}/children'
        children_data = self._magento_api_call(url) or []
        conf_skus = []
        sku_price_list = [
            {'name': child.get('name'), 'sku': child.get('sku'), 'price': child.get('price')}
            for child in children_data
            if 'sku' in child and 'price' in child
        ]

        if sku_price_list:
            min_price = min(sku['price'] for sku in sku_price_list)

            conf_skus = [
                {# 'sku': sku['sku'].split('-')[-1],
                'sku': sku['name'].split('-')[-1], # sku'lara sürekli müdahele edildiği için name'in sonunu alıyorum sku için.
                'price': round(sku['price'] - min_price, 2)}
                for sku in sku_price_list
            ]

        return conf_skus

    def fetch_option_name_and_translate(self):

        pass