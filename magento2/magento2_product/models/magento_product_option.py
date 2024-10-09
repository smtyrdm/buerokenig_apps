from odoo import models, fields, api
import json
import logging
import ast

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    magento_json_data = fields.Text(string='JSON Data', tracking=False)

    def action_magento_option(self):
        for rec in self:
            self.env['product.fetch.wizard'].fetch_product_option(rec)
            #if rec.magento_json_data:
            data = json.loads(rec.magento_json_data or "[]")
            unmatched_titles = set()

            for item in data:
                title = item.get('title')
                if title:
                    matched = False
                    for ptal in rec.attribute_line_ids:
                        if (
                                (ptal.label and ptal.label == title) or
                                (ptal.label and ptal.label in title) or
                                (ptal.label and title in ptal.label) or
                                ptal.attribute_id.name == title or
                                ptal.attribute_id.name in title or
                                title in ptal.attribute_id.name
                        ):
                            ptal.magento_option = title
                            matched = True
                            self.match_values_with_attribute_line(ptal, item.get('values', []))
                            break
                        elif ptal.magento_option == title:
                            matched = True
                            self.match_values_with_attribute_line(ptal, item.get('values', []))
                            break

                    if not matched:
                        check_skus = item.get('values', [])
                        sku_check_results = ['sku' in sku for sku in check_skus]
                        if any(sku_check_results):
                            unmatched_titles.add(title)

            if unmatched_titles:
                unmatched_titles_str = ', '.join(unmatched_titles)
                log_data = {
                    'message': f"Eşleşmeyen title'lar: {unmatched_titles_str}",
                    'name': 'magento_ptal_title',
                    'path': f"Product: {rec.name}",
                    'func': f"Titlelar Eşleşmiyor",
                    'line': rec.magento_sku,
                }

                self.log_if_not_exists(log_data)

    def match_values_with_attribute_line(self, ptal, values):
        unmatched_values = set()

        for value in values:
            value_title = value.get('title', '')
            value_sku = value.get('sku', '')
            value_price = value.get('price', 0)
            matched = False

            for rec in ptal.value_ids:
                # İlk koşul kontrolü
                if (
                        ptal.magento_option and
                        isinstance(rec.variant_suffix, str) and rec.variant_suffix == value_sku or
                        isinstance(rec.name, str) and rec.name == value_title
                ):
                    ptav = self.env['product.template.attribute.value'].search([
                        ('product_attribute_value_id', '=', rec.id),
                        ('attribute_line_id', '=', ptal.id)
                    ], limit=1)
                    ptav.price_extra = value_price
                    _logger.warning(f'SKU İlk if: {value_sku}')
                    matched = True
                    break

            # İkinci koşul kontrolü sadece ilk koşul sağlanmazsa
            if not matched:
                for rec in ptal.value_ids:
                    if (
                            (isinstance(rec.variant_suffix, str) and isinstance(value_sku,
                                                                                str) and rec.variant_suffix in value_sku) or
                            (isinstance(value_sku, str) and isinstance(rec.variant_suffix,
                                                                       str) and value_sku in rec.variant_suffix)
                    ):
                        ptav = self.env['product.template.attribute.value'].search([
                            ('product_attribute_value_id', '=', rec.id),
                            ('attribute_line_id', '=', ptal.id)
                        ], limit=1)
                        ptav.price_extra = value_price
                        _logger.warning(f'SKU İkinci if: {value_sku}')
                        matched = True
                        break

            if not matched:
                unmatched_values.add(f'Title: {value_title} Sku: {value_sku}')

        if unmatched_values:
            unmatched_values_str = ', '.join(unmatched_values)
            log_data = {
                'message': f"Eşleşmeyen değerler: {unmatched_values_str}",
                'name': 'magento_ptav_name',
                'path': f"Product: {ptal.product_tmpl_id.name}",
                'func': f"Title: {ptal.attribute_id.name}, SKU: {ptal.product_tmpl_id.magento_sku}",
                'line': ptal.id,
            }

            self.log_if_not_exists(log_data)

    def log_if_not_exists(self, log_data, email=False):
        existing_log = self.env['ir.logging'].search([
            ('name', '=', log_data.get('name')),
            ('message', '=', log_data.get('message')),
            ('path', '=', log_data.get('path')),
            ('func', '=', log_data.get('func')),
            ('line', '=', log_data.get('line'))
        ], limit=1)

        if not existing_log:
            self.env['ir.logging'].magento_ir_logging(log_data, email=email)

    # compute_dynmaic_fields = fields.Boolean(string='Compute Dynmaic Fields', compute='_compute_dynmaic_fields')
    #
    # def _compute_dynmaic_fields(self):
    #     if self.attribute_line_ids:
    #         self.compute_dynmaic_fields = True
    #         for rec in self.attribute_line_ids:
    #             rec.magento_attribute_titles(self.id)
    #     else:
    #         self.compute_dynmaic_fields = False
    #
    # def update_attribute_values_from_magento(self):
    #
    #     try:
    #         magento_data = json.loads(self.magento_json_data)
    #     except json.JSONDecodeError as e:
    #         raise ValueError(f"JSON formatında hata: {e}")
    #     for data in magento_data:
    #         for value in data.get('values', {}):
    #             sku = value.get('sku')
    #             price_extra = value.get('price')
    #             name = value.get('title')
    #
    #             if sku and price_extra:
    #                 attribute_value = self.env['product.template.attribute.value'].search([
    #                     ('product_tmpl_id', '=', self.id),
    #                     '|',
    #                     ('product_attribute_value_id.variant_suffix', '=', sku),
    #                     ('product_attribute_value_id.name', '=', name)
    #                 ], limit=1)
    #
    #                 if attribute_value:
    #                     attribute_value.write({'price_extra': price_extra})
    #                 else:
    #                     print(f"SKU: {sku}")


class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    magento_option = fields.Char(string="Magento Option")

    @api.model
    def dynamic_magento_option(self):
        # <field name="magento_option" widget="dynamic_dropdown" options="{'values':'_dynamic_magento_option'}" context="{'product_tmpl_id': product_tmpl_id}"/>
        values = []; active_id = self.env.context.get('id', '')
        ptal = self.env['product.template.attribute.line'].browse(active_id) if active_id else False
        magento_option = ptal.magento_option if ptal and ptal.magento_option else ""
        product_tmpl_id = self.env.context.get('product_tmpl_id', '')
        product_template = self.env['product.template'].browse(product_tmpl_id) if product_tmpl_id else False
        if product_template:
            for m_ptal in json.loads(product_template.magento_json_data or "[]"):
                title = m_ptal.get('title', '')
                #valid_values = [value for value in option.get('values', []) if value.get('sku')]
                if magento_option == title:
                    values.append((f"{title}", f"{title}")); continue
                if title not in product_template.attribute_line_ids.mapped('magento_option'):
                    values.append((f"{title}", f"{title}"))
        return values

    def write(self, vals):
        # burda yapılan product.template çok beklemesini engelliyor.
        if 'magento_option' in vals and len(vals) == 1:
            query = """
                UPDATE product_template_attribute_line
                SET magento_option = %s
                WHERE id = %s
            """
            if not vals['magento_option']:
                vals['magento_option'] = ''
            self.env.cr.execute(query, (vals['magento_option'], self.id))
            self.invalidate_cache(['magento_option'])
            return True
        return super(ProductTemplateAttributeLine, self).write(vals)

    def action_open_ptal_magento(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'PTAL Related Model',
            'view_mode': 'form',
            'res_model': 'product.template.attribute.line',
            'res_id': self.id,
            'target': 'new',  # çünkü veri çoksa sayfa baya bekliyor.
        }


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    magento_option_value = fields.Char(string="Magento Option")

    @api.model
    def dynamic_magento_option_value(self):
        # <field name="magento_option_value" widget="dynamic_dropdown" options="{'values':'dynamic_magento_option'}" context="{'product_tmpl_id': product_tmpl_id}"/>
        values = []
        attribute_line_id = self.env.context.get('attribute_line_id', '')
        active_id = self.env.context.get('id', '')
        ptav = self.env['product.template.attribute.value'].browse(active_id) if active_id else False
        magento_option_value = json.loads(ptav.magento_option_value or "[]") if ptav and ptav.magento_option_value else ""
        attribute_line = self.env['product.template.attribute.line'].browse(attribute_line_id) if attribute_line_id else False
        if attribute_line:
            magento_option = attribute_line.magento_option or "Boş"
            for m_ptav in json.loads(attribute_line.product_tmpl_id.magento_json_data or "[]"):
                if m_ptav.get("title", "") == magento_option:
                    for value in m_ptav.get('values', []):
                        val = {"title": value.get('title', ""), "sku": value.get('sku', ""), "price": value.get('price', 0)}
                        mov = attribute_line.product_template_value_ids.mapped('magento_option_value')
                        mov = [json.loads(val) for val in mov if val]
                        # önceden seçilen varsa seçileninde gözükmesi için
                        if magento_option_value == val:
                            values += [(json.dumps(val), json.dumps(val)),]
                            continue
                        if val not in mov:
                            values += [(json.dumps(val), json.dumps(val)),]

        return values

    def write(self, vals):
        if 'magento_option_value' in vals:
            if vals['magento_option_value'] == False:
                vals['price_extra'] = 0
            else:
                vals['price_extra'] = json.loads(vals['magento_option_value'] or "[]").get('price', 0)
        return super(ProductTemplateAttributeValue, self).write(vals)

    @api.model
    def create(self, vals):
        if 'magento_option_value' in vals:
            if vals['magento_option_value'] == False:
                vals['price_extra'] = 0
            else:
                vals['price_extra'] = json.loads(vals['magento_option_value'] or "[]").get('price', 0)
        return super(ProductTemplateAttributeValue, self).create(vals)

#
#
#     @api.model
#     def magento_attribute_titles(self,id = ""):
#         if id:
#             product_template = self.env['product.template'].browse(id)
#             if not product_template.magento_json_data:
#                 return []
#             try:
#                 json_data = json.loads(product_template.magento_json_data)
#             except json.JSONDecodeError:
#                 return []
#
#             titles = set()
#             for item in json_data:
#                 titles.add(item.get('title', ''))
#
#             return [(title, title) for title in titles]
#         else:
#             return []
#
#     magento_attribute_title = fields.Selection(selection='magento_attribute_titles',
#                                                string='Magento Attribute Title')

# class ProductCategory(models.Model):
#     _inherit = 'product.category'
#
#     magento_name = fields.Char(string="Magento Name")
#     magento_id = fields.Char(string="Magento ID")


