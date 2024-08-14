import logging

from odoo import models, fields, exceptions, _

_logger = logging.getLogger(__name__)


class ProductFetchWizard(models.Model):
    _name = 'product.fetch.wizard'
    _description = 'Product Fetch Wizard'

    product_type = fields.Selection([
        ('simple', 'Simple Products'),
        ('configurable', 'Configurable Products'),
    ], string="Product Type", required=True, default='simple')

    def fetch_products(self):
        """Fetch products from Magento"""
        product_type = self.product_type
        search_criteria = f'searchCriteria[filterGroups][0][filters][0][field]=type_id&searchCriteria[filterGroups][0][filters][0][value]={product_type}'
        url = f'/rest/all/V1/products?{search_criteria}&searchCriteria%5BpageSize%5D=5&searchCriteria%5BcurrentPage%5D=1'
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
        buy_route = self.env['stock.location.route'].search([('name', '=', 'Buy')], limit=1)
        vendor = self.env['res.partner'].search([('name', '=', 'Tischkönig GmbH'),('route_ids', 'in', buy_route.ids)], limit=1)
        product_template = self.env['product.template'].search([('default_code', '=', item['sku'])])
        existing_seller = product_template.seller_ids.filtered(lambda s: s.name.id == vendor.id)
        values = {
            'name': item['name'],
            'default_code': item['sku'],
            'list_price': item.get('price', 0.0),
            'type': 'product',
            'magento': True,
            'route_ids': [(6, 0, [dropship_route.id])] , # Dropship rotasını ekle
        }

        # Eğer mevcut bir satıcı yoksa, yeni satıcı ekle
        if not existing_seller:
            values['seller_ids'] = [(0, 0, {'name': vendor.id})]  # Vendor id'sini ekle

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