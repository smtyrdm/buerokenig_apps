import logging

from odoo import models, fields, exceptions, _
import urllib.parse
import base64
import requests

_logger = logging.getLogger(__name__)


class ProductFetchWizard(models.Model):
    _name = 'product.fetch.wizard'
    _description = 'Product Fetch Wizard'

    sku = fields.Char(string="SKU")
    product_type = fields.Selection([('simple', 'Simple'),
                                     ('configurable', 'Configurable'),
                                     ('update_price', 'Update Price'),
                                     ('update_product_name', 'Update Product Name'),
                                     ], string="Product Type", )

    def fetch_products(self):
        """Fetch products from Magento"""
        if self.product_type == 'category':
            self.fetch_category()
        elif self.product_type == 'update_price':
            self._update_product_price()
        elif self.product_type == 'update_product_name':
            self._update_product_name()
        else:
            if self.sku:
                self._fetch_product_by_sku(self.sku)
            else:
                self._fetch_products_by_type()

    def _fetch_product_by_sku(self, sku):
        """Fetch a specific product by SKU from Magento"""
        url = f'/rest/all/V1/products/{urllib.parse.quote(sku)}'
        item = self._magento_api_call(url)
        if not item:
            return
        try:
            domain = ['|', '|', ('default_code', '=', item['sku']), ('variant_code', '=', item['sku']), '&',
                      ('magento_product_id', '=', item['id']), ('name', '=', item['name'])]
            product_template = self.env['product.template'].search(domain)  # variant_code
            if not product_template:
                self._process_product(item)
        except Exception as e:
            _logger.info("Exception occured 11 %s", e)
            raise exceptions.UserError(_("Error Occured 11 %s") % e)

    def _fetch_products_by_type(self):
        """Fetch products by type from Magento"""
        if self.product_type == 'simple':
            url = (
                f'/rest/all/V1/products?'
                f'searchCriteria[filterGroups][0][filters][0][field]=type_id&'
                f'searchCriteria[filterGroups][0][filters][0][value]={self.product_type}&'
                f'searchCriteria[filterGroups][1][filters][0][field]=visibility&'
                f'searchCriteria[filterGroups][1][filters][0][value]=4'
            )
        else:
            # Diğer türler için visibility filtresi eklenmeden URL
            url = (
                f'/rest/all/V1/products?'
                f'searchCriteria[filterGroups][0][filters][0][field]=type_id&'
                f'searchCriteria[filterGroups][0][filters][0][value]={self.product_type}'
            )
        magento_products = self._magento_api_call(url)

        if not magento_products:
            return
        try:
            items = magento_products.get('items', [])
            for item in items:
                domain = ['|', '|', ('default_code', '=', item['sku']), ('variant_code', '=', item['sku']), '&',
                          ('magento_product_id', '=', item['id']), ('name', '=', item['name'])]
                product_template = self.env['product.template'].search(domain)  # variant_code
                if product_template:
                    continue
                self._process_product(item)
        except Exception as e:
            _logger.info("Exception occured 22 %s", e)
            raise exceptions.UserError(_("Error Occured 22 %s") % e)

    def _magento_api_call(self, url, method='GET', headers=None):
        """Call Magento API and return the response"""
        try:
            return self.env['magento.connector'].magento_api_call(headers=headers or {}, url=url, type=method)
        except Exception as e:
            _logger.info("Magento API call failed: %s", e)
            raise exceptions.UserError(_("Error Occurred %s") % e)

    def _process_product(self, item):
        """Process each product item from Magento"""
        translated_routes = self.env['ir.translation'].sudo().search([
            ('name', '=', 'stock.location.route,name'),
            ('src', '=', 'Dropship'),
            ('res_id', '!=', False)
        ])
        route_ids = list(set(translated_routes.mapped('res_id')))
        if route_ids:
            dropship_route = self.env['stock.location.route'].sudo().browse(route_ids[0])
        else:
            raise models.ValidationError("Dropship route not found in any language.")

        vendor = self.env['res.partner'].search(
            [('name', '=', 'Tischkönig GmbH'), ('email', '=', 'verkauf@tischkoenig.de')], limit=1)
        if not vendor:
            raise models.ValidationError("{Vendor not!}")
        custom_attributes = item.get("custom_attributes", [])
        url_key_value = next(
            (data.get("value", "") for data in custom_attributes if data.get("attribute_code", "") == "url_key"), False)
        category = False
        for name in item['name'].split():
            category1 = self.env['product.category'].search([('name', '=', name)])
            category2 = self.env['product.category'].search([('name', '=', name.replace('u', 'ü'))])
            if category1 or category2:
                category = category1 or category2
                break

        values = {
            'name': item['name'],
            'default_code': item['sku'],
            'variant_code': item['sku'],
            'magento_sku': item['sku'],
            'list_price': item.get('price', 0.0),
            'type': 'product',
            'magento': True,
            'magento_product_id': item['id'],
            'magento_url_key': url_key_value or False,
            'image_1920': self._get_image(item) or False,
            'route_ids': [(6, 0, [dropship_route.id])],  # Dropship rotasını ekle
            'seller_ids': [(0, 0, {'name': vendor.id})],
        }
        if category:
            values['categ_id'] = category.id
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
            url = f'/rest/all/V1/products/{urllib.parse.quote(sku)}?storeId={store.store_id}'
            magento_product = self._magento_api_call(url)
            if magento_product:
                names[store.lang_id.code] = magento_product.get('name', '')

        return names

    def _get_image(self, item):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_host = ICPSudo.get_param('magento2.magento_host')
        custom_attributes = item.get("custom_attributes", [])
        image_value = next(
            (data.get("value", "") for data in custom_attributes if data.get("attribute_code", "") == "image"), False)
        if magento_host and image_value:
            image_url = 'https://' + magento_host + '/media/catalog/product/' + image_value
            response = requests.get(image_url)
            if response.ok and response.content:
                image_base64 = base64.b64encode(response.content)
            else:
                image_base64 = False
            return image_base64
        else:
            return False

    def _update_product_price(self):
        """Update product prices based on their variants' lowest price in Magento."""
        products = self.env['product.template'].search([('magento', '=', True)])

        for product in products:
            url = f'/rest/V1/configurable-products/{urllib.parse.quote(product.variant_code or product.default_code)}/children'
            children_products = self._magento_api_call(url)

            if not children_products:
                continue

            prices = [child.get('price', 0.0) for child in children_products if 'price' in child]
            if not prices:
                continue

            min_price = min(prices)

            product.sudo().write({'list_price': min_price})

    def _update_product_name(self):
        """Update product names based on their variants"""
        products = self.env['product.template'].search([('magento', '=', True)])
        for product in products:
            sku = product.variant_code or product.default_code
            if not sku:
                continue
            self._update_translations(product.id,sku)

    # def fetch_category(self):
    #     url = '/rest/V1/categories'
    #     type = 'GET'
    #
    #     magento_category = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
    #
    #     try:
    #         children_data = magento_category.get('children_data',[])
    #         for parent in children_data:
    #             if not parent.get('children_data',[]):
    #
    #                 odoo1 = self.env['product.category'].search([('name', 'ilike', parent['name'])])
    #                 if not odoo1:
    #                     continue
    #                 odoo1.write({
    #                     'magento_name': parent['name'],
    #                     'magento_id': parent['id'],
    #                 })
    #             for children in parent.get('children_data',[]):
    #                 odoo2= self.env['product.category'].search([('name', 'ilike', children['name'])])
    #                 if not odoo2:
    #                     continue
    #                 odoo2.write({
    #                     'magento_name': children['name'],
    #                     'magento_id': children['id'],
    #                 })
    #     except Exception as e:
    #         _logger.info("Exception occured %s", e)
    #         raise exceptions.UserError(_("Error Occured %s") % e)
