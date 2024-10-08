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
    product_type = fields.Selection([('SKU', 'SKU'),
                                     ('simple', 'Simple'),
                                     ('configurable', 'Configurable'),
                                     ('update_price', 'Update Price'),
                                     ('update_product_name', 'Update Product Name')
                                     ], string="Product Type", )

    def fetch_products(self):
        """Fetch products from Magento"""
        if self.product_type == 'SKU' and self.sku:
            self._fetch_product_by_sku(self.sku)
        elif self.product_type in ['simple', 'configurable']:
            self._fetch_products_by_type()
        elif self.product_type == 'update_price':
            self._update_product_price()
        elif self.product_type == 'update_product_name':
            self._update_product_name()

    def _fetch_product_by_sku(self, sku):
        """Fetch a specific product by SKU from Magento"""
        url = f'/rest/all/V1/products/{urllib.parse.quote(sku)}'
        item = self._magento_api_call(url)
        if not item.get('sku', ''):
            data = {
                'message': f"Bu SKU'ya ait bir ürün bulunamadı: {sku}",
                'path': "SKU CONTROL ET",
                'func': sku,
                'line': 'N/A',
            }
            self.env['ir.logging'].magento_ir_logging(data,email=False)
            return
        try:
            domain = [('magento_sku', '=', item.get('sku', ''))]
            product_template = self.env['product.template'].search(domain)  # variant_code

            if not product_template:
                self._process_product(item)
        except Exception as e:
            _logger.info("Exception occured 11 %s", e)
            raise exceptions.UserError(_("Error Occured 11 %s") % e)

    def _fetch_products_by_type(self):
        """Fetch products by type from Magento"""
        if self.product_type == 'simple':
            # conf simple ayırt etmek için visibility: 4 -> (store açık demek.)
            url = (
                f'/rest/all/V1/products?'
                f'searchCriteria[filterGroups][0][filters][0][field]=type_id&'
                f'searchCriteria[filterGroups][0][filters][0][value]={self.product_type}&'
                f'searchCriteria[filterGroups][1][filters][0][field]=visibility&'
                f'searchCriteria[filterGroups][1][filters][0][value]=4&'
                f'searchCriteria[filterGroups][2][filters][0][field]=status&'
                f'searchCriteria[filterGroups][2][filters][0][value]=1'
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
                domain = [('magento_sku', '=', item.get('sku', ''))]
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
            'magento_type': item.get('type_id', ''),
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
            if not name:
                data = {
                    'message': f"Bu ürünün name alanında translate değerleri eksik: {sku}",
                    'name': 'magento_pt_name',
                    'path': f"Lang : {lang_code}",
                    'func': sku,
                    'line': 'N/A',
                }
                self.env['ir.logging'].magento_ir_logging(data, email=False)
                continue

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

        def magento_log(product, message, path, name="magento"):
            data = {
                'message': f"{message}: {product.magento_sku}",
                'name': name,
                'path': path,
                'func': product.magento_sku,
                'line': 'N/A',
            }
            self.env['ir.logging'].magento_ir_logging(data, email=False)

        products = self.env['product.template'].search([('magento', '=', True)])

        for product in products:
            url = (f"/rest/V1/products/{urllib.parse.quote(product.magento_sku)}"
                   if product.magento_type == 'simple' else
                   f"/rest/V1/configurable-products/{urllib.parse.quote(product.magento_sku)}/children")
            children_products = self._magento_api_call(url)

            if not children_products:
                continue

            prices = [child.get('price', 0.0) for child in
                      (children_products if product.magento_type == 'configurable' else [children_products])]
            if not prices:
                magento_log(product, "Bu ürünün fiyat bilgileri eksik", f"{product.magento_type} : Ürün Fiyati Eksik", 'magento_pt_price')
                continue

            if product.magento_type == 'simple' and children_products.get('type_id', '') != product.magento_type:
                magento_log(product, "Product Type'ları uyumsuz. Lütfen Kontrol Edin", "Product Type'ları uyumsuz", 'magento_pt_type')
                continue

            min_price = min(prices)
            product.sudo().write({'list_price': min_price})

            if product.magento_type not in ['simple', 'configurable']:
                magento_log(product, "Ürün Type'ı belirtilmemiş bu yüzden fiyat çekimi yapılamıyor","Ürün Type'ı belirtilmemiş", 'magento_pt_type')

    def _update_product_name(self):
        """Update product names based on their variants"""
        products = self.env['product.template'].search([('magento', '=', True)])
        for product in products:
            sku = product.magento_sku
            if not sku:
                continue
            self._update_translations(product.id, sku)
