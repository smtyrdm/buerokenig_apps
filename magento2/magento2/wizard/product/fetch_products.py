import logging

from odoo import models, fields, exceptions, _

_logger = logging.getLogger(__name__)


class ProductFetchWizard(models.Model):
    _name = 'product.fetch.wizard'
    _description = 'Product Fetch Wizard'

    # def fetch_products(self):
    #     """Fetch products from Magento"""
    #     url = '/rest/all/V1/products?searchCriteria%5BpageSize%5D=5&searchCriteria%5BcurrentPage%5D=1'
    #     type = 'GET'
    #     magento_products = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
    #     try:
    #         items = magento_products.get('items', [])
    #         for i in items:
    #             products = self.env['magento.product'].search([('sku', '=', i['sku'])])
    #             values = {
    #                 'sku': i['sku'],
    #                 'name': i['name'],
    #                 'price': i.get('price', 0.0),
    #                 'status': str(i.get('status', 0)),
    #                 'type': i.get('type_id'),
    #                 'visibility': str(i.get('visibility')),
    #             }
    #             if products:
    #                 products.sudo().write(values)
    #             else:
    #                 self.env['magento.product'].sudo().create(values)
    #
    #     except Exception as e:
    #         _logger.info("Exception occurred %s", e)
    #         raise exceptions.UserError(_("Error Occurred %s") % e)

    def fetch_products(self):
        """Fetch products from Magento"""
        url = '/rest/all/V1/products?searchCriteria%5BpageSize%5D=5&searchCriteria%5BcurrentPage%5D=1'
        magento_products = self._magento_api_call(url)

        if not magento_products:
            return

        items = magento_products.get('items', [])
        for item in items:
            self._process_product(item)

    def _magento_api_call(self, url, method='GET', headers=None):
        """Call Magento API and return the response"""
        try:
            return self.env['magento.connector'].magento_api_call(headers=headers or {}, url=url, type=method)
        except Exception as e:
            _logger.info("Magento API call failed: %s", e)
            raise exceptions.UserError(_("Error Occurred %s") % e)

    def _process_product(self, item):
        """Process each product item from Magento"""
        dropship_route = self.env['stock.location.route'].search([('name', '=', 'Dropship')], limit=1)
        product_template = self.env['product.template'].search([('default_code', '=', item['sku'])])
        values = {
            'name': item['name'],
            'default_code': item['sku'],
            'list_price': item.get('price', 0.0),
            'type': 'product',
            'magento': True,
            'route_ids': [(6, 0, [dropship_route.id])]  # Dropship rotasını ekle
        }

        if product_template:
            product_template.sudo().write(values)
        else:
            product_template = self.env['product.template'].sudo().create(values)

        self._update_translations(product_template.id, item['sku'])

    def _update_translations(self, res_id, sku):
        """Update product translations in multiple languages"""
        names = self._fetch_product_names(sku)
        for lang_code, name in names.items():
            translation = self.env['ir.translation'].sudo().search([
                ('name', '=', 'product.template,name'),
                ('res_id', '=', res_id),
                ('lang', '=', lang_code),
                ('type', '=', 'model')
            ], limit=1)

            if translation:
                translation.write({'value': name})
            else:
                self.env['ir.translation'].sudo().create({
                    'name': 'product.template,name',
                    'res_id': res_id,
                    'lang': lang_code,
                    'value': name,
                    'state': 'translated',
                    'type': 'model',
                })

    def _fetch_product_names(self, sku):
        """Fetch product names for different store views from Magento"""
        names = {}
        stores = self.env['magento.stores'].search([('lang_id', '!=', None)])
        for store in stores:
            url = f'/rest/all/V1/products/{sku}?storeId={store.store_id}'
            magento_product = self._magento_api_call(url)
            if magento_product:
                names[store.lang_id.code] = magento_product.get('name', '')

        return names