from odoo import models, fields, api
import json

import ast
from rapidfuzz import fuzz

# Benzerlik oranı -> fuzz.ratio(string1, string2)
# Kısmi eşleşme -> fuzz.partial_ratio(string1, string2)
# Token set eşleşmesi ->fuzz.token_set_ratio("apple banana orange", "banana apple grape")
import logging
_logger = logging.getLogger(__name__)


# magento_json_data -> cron veya action
# magento_option -> manuel veya depends('magento_json_data')
# magento_option_value -> çoğunluk depends('magento_option') veya manuel


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    magento_json_data = fields.Text(string='JSON Data', tracking=False, store=True,readonly=False )

    def action_magento_option(self):
        for rec in self:
            self.env['product.fetch.wizard'].fetch_product_option(rec)




class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    magento_option = fields.Char(string="Magento Option", compute="_compute_magento_option", store=True, readonly=False)

    # magento_values_data = fields.Char(string="Magento Values Data")
    @api.depends('product_tmpl_id.magento_json_data')
    def _compute_magento_option(self):
        sku = self[0].product_tmpl_id.magento_sku or self[0].product_tmpl_id.variant_code or self[0].product_tmpl_id.default_code or ''
        ir_data = {'name': 'magento_ptal_title', 'message': [], 'line': sku, 'path': [], 'func':'_compute_magento_option'}
        ir_data["message"]=[];ir_data['path']=[]
        data = json.loads(self[0].product_tmpl_id.magento_json_data or "[]") if self and self[0].product_tmpl_id else []
        for ptal in self:
            ir_log = True
            for m_ptal in data:
                # values sku yoksa bu ptal seçimide yoktur o zaman log hata basmaz bu sayede
                valid_values = [value for value in m_ptal.get('values', [])if value.get('sku')]
                title = m_ptal.get('title', '')
                if valid_values and any(fuzz.partial_ratio(option, title) == 100 for option in [ptal.magento_option, ptal.label, ptal.attribute_id.name] if option):
                    ptal.magento_option = title
                    data.remove(m_ptal); ir_log = False; break
            name = ptal.attribute_id.name
            if ir_log and name and ptal.product_tmpl_id.id == self[0].product_tmpl_id.id:
                self.ir_log_search(ir_data, 'message', ptal.attribute_id.name)
        for m_ptal in data:
            # values sku yoksa bu ptal seçimide yoktur o zaman log hata basmaz bu sayede
            valid_values = [value for value in m_ptal.get('values', []) if value.get('sku')]
            if valid_values and m_ptal.get('title', ''):
                self.ir_log_search(ir_data, 'path', m_ptal.get('title', ''))
        if ir_data['message'] or ir_data['path']:
            self[0].sudo().env['ir.logging'].magento_ir_logging(ir_data, email=False)
        del ir_data['message']; del ir_data['path']


    def ir_log_search(self, ir_data, path_message, search):
        log = False
        ir_log_data = self.sudo().env['ir.logging'].search([('name', '=', ir_data.get('name')), ('line', '=',  ir_data.get('line'))])
        for ir_log in ir_log_data:
            path = ir_log.path; message=ir_log.message
            if path_message == "path" and fuzz.partial_ratio(path, search) > 90 or search in path:
                log = True;break
            if path_message == "message" and fuzz.partial_ratio(message, search) > 90 or search in message:
                log = True;break
        if not ir_log_data or not log:
            ir_data[path_message].append(f"{search}")
        return ir_data


    @api.model
    def dynamic_magento_option(self):
        # <field name="magento_option" widget="dynamic_dropdown" options="{'values':'_dynamic_magento_option'}" context="{'product_tmpl_id': product_tmpl_id}"/>
        values = [];
        active_id = self.env.context.get('id', '')
        ptal = self.env['product.template.attribute.line'].browse(active_id) if active_id else False
        magento_option = ptal.magento_option if ptal and ptal.magento_option else ""
        product_tmpl_id = self.env.context.get('product_tmpl_id', '')
        product_template = self.env['product.template'].browse(product_tmpl_id) if product_tmpl_id else False
        if product_template:
            for m_ptal in json.loads(product_template.magento_json_data or "[]"):
                # values sku yoksa bu ptal seçimide yoktur o zaman
                valid_values = [value for value in m_ptal.get('values', [])if value.get('sku')]
                title = m_ptal.get('title', '')
                if valid_values and magento_option == title:
                    values.append((f"{title}", f"{title}"));
                    continue
                if valid_values and title not in product_template.attribute_line_ids.mapped('magento_option'):
                    values.append((f"{title}", f"{title}"))
        return values

    def write(self, vals):
        # burda yapılan product.template çok beklemesini engelliyor.
        if 'magento_option' in vals and len(vals) == 1:
            if not vals['magento_option']:
                ptav = """UPDATE product_template_attribute_value SET magento_option_value = %s,  price_extra = %s  WHERE attribute_line_id = %s"""
                self.env.cr.execute(ptav, ('',0, self.id))
                vals['magento_option'] = ''

            ptal = """UPDATE product_template_attribute_line SET magento_option = %s WHERE id = %s"""
            self.env.cr.execute(ptal, (vals['magento_option'], self.id))
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

    magento_option_value = fields.Char(string="Magento Option", compute="_compute_magento_option_value", store=True, readonly=False)

    @api.depends('attribute_line_id.magento_option')
    def _compute_magento_option_value(self):
        product_sku = self[0].product_tmpl_id.magento_sku or self[0].product_tmpl_id.variant_code or self[0].product_tmpl_id.default_code or ''
        ir_data = {'name': 'magento_ptav_title', 'message': [], 'line': product_sku, 'path':[], 'func':'_compute_magento_option_value'}
        ir_data["message"] = [];ir_data['path'] = []
        data = json.loads(self[0].product_tmpl_id.magento_json_data or "[]") if self and self[0].product_tmpl_id else []
        list_values = {}
        for ptav in self:
            magento_option = ptav.attribute_line_id.magento_option;ir_log = True
            if list_values.get(magento_option,''):
                values = list_values.get(magento_option)
            else:
                values = next((item.get('values', []) for item in data if item.get('title', '') == magento_option), [])
            list_values[magento_option] = values
            for val in values: #(val1 for val1 in values if val1 not in not_val):
                title_sku = {"title": val.get('title', ""), "sku": val.get('sku', "")}
                o_mov = json.loads(ptav.magento_option_value or "{}");o_mov.pop('price', None)
                sku = ptav.variant_suffix if ptav.variant_suffix else ""
                name = ptav.name if ptav.name else ""
                if fuzz.partial_ratio(json.dumps(title_sku), json.dumps(o_mov)) == 100 and fuzz.ratio(sku, title_sku['sku']) == 100:
                    ir_log = False
                elif fuzz.ratio(sku, title_sku['sku']) == 100 and fuzz.partial_ratio(name or "", title_sku['title']) == 100:
                    ir_log = False
                elif fuzz.ratio(sku, title_sku['sku']) == 100:
                    _logger.warning("1")
                    _logger.warning(f"{magento_option}")
                    _logger.warning(f"{title_sku['sku']}")
                    ir_log = False
                if not ir_log:
                    _logger.warning("2")
                    ptav.magento_option_value = json.dumps(title_sku | {"price": val.get('price', 0)})
                    ptav.price_extra = val.get('price', 0)
                    list_values[magento_option].remove(val);break
            # if ir_log:
            #     ptav.magento_option_value = False;ptav.price_extra = 0
            #     search= {ptav.name:ptav.variant_suffix}
            #     if search not in ir_data["message"] and magento_option: #and ptav.attribute_line_id == self[0].attribute_line_id:
            #         self.ir_log_search(ir_data,'message', search)

        for ptav in self:
            magento_option = ptav.attribute_line_id.magento_option
            ir_log = True; sku = ptav.variant_suffix or "boş"
            for val in list_values.get(magento_option):
                if fuzz.partial_ratio(sku, val.get('title', "")) == 100 and len(sku) == len(val.get('sku', "")):
                    ptav.magento_option_value = json.dumps(title_sku | {"price": val.get('price', 0)})
                    ptav.price_extra = val.get('price', 0)
                    list_values[magento_option].remove(val);ir_log = False;break
            if ir_log:
                ptav.magento_option_value = False;ptav.price_extra = 0
                search= {ptav.name:ptav.variant_suffix}
                if search not in ir_data["message"] and magento_option: #and ptav.attribute_line_id == self[0].attribute_line_id:
                    self.ir_log_search(ir_data,'message', search)

        list_values = {key: value for key, value in list_values.items() if value}
        for key, value in list_values.items():
            search = {key: value}
            self[0].ir_log_search(ir_data, 'path', search)
        if ir_data['message'] or ir_data['path']:
            self[0].sudo().env['ir.logging'].magento_ir_logging(ir_data, email=False)
        del ir_data['message'];del ir_data['path']



    def ir_log_search(self, ir_data, path_message, search):
        search = str(search); log=False
        ir_log_data = self.sudo().env['ir.logging'].search([('name', '=', ir_data.get('name','')),('line', '=', ir_data.get('line',''))])
        for ir_log in ir_log_data:
            path = ir_log.path; message = ir_log.message
            if path_message == "path" and fuzz.partial_ratio(path, search) > 90 or search in path:
                log = True;break
            if path_message == "message" and fuzz.partial_ratio(message, search) > 90 or search in message:
                log = True;break
        if not ir_log_data or not log:
            ir_data[path_message].append(f"{search}")
        return ir_data


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
                            values += [(json.dumps(val), json.dumps(val)), ]
                            continue
                        if val not in mov:
                            values += [(json.dumps(val), json.dumps(val)), ]
        return values

    def write(self, vals):
        if 'magento_option_value' in vals:
            if vals['magento_option_value'] == False:
                vals['price_extra'] = 0
            else:
                vals['price_extra'] = json.loads(vals['magento_option_value'] or "{}").get('price', 0)
        return super(ProductTemplateAttributeValue, self).write(vals)

    @api.model
    def create(self, vals):
        if 'magento_option_value' in vals:
            if vals['magento_option_value'] == False:
                vals['price_extra'] = 0
            else:
                vals['price_extra'] = json.loads(vals['magento_option_value'] or "{}").get('price', 0)
        return super(ProductTemplateAttributeValue, self).create(vals)

# values += [(f'{val}', f'{val}'),]
# vals['price_extra'] = ast.literal_eval(vals['magento_option_value'] or "{}").get('price', 0)
# ptal.env.cr.flush()



        # # magento_json_data eşleşme olmayanları log basılacak. misal starke data içinde yok ama odoo da var. tam tersi olsa habire starke log düşecek.
        # assigned_ptal_ids = set()
        # for m_ptal in data:
        #     title = m_ptal.get('title', '');
        #     ir_log = True
        #     for ptal in self.filtered(lambda p: p.id not in assigned_ptal_ids):
        #         if any(fuzz.partial_ratio(option, title) == 100 for option in [ptal.magento_option, ptal.label, ptal.attribute_id.name] if option):
        #             ptal.magento_option = title
        #             ir_log = False;assigned_ptal_ids.add(ptal.id);break
        #     if ir_log and not self.sudo().env['ir.logging'].search([('name', '=', 'magento_ptal_title'), ('line', '=', sku), ('message', 'ilike', title)]):
        #         ir_data["message"].append(title)
        # if ir_data['message'] or not data:
        #     self[0].sudo().env['ir.logging'].magento_ir_logging(ir_data, email=False)



        # for rec in self:
        #     magento_option = rec.attribute_line_id.magento_option
        #     values = next((item.get('values', []) for item in data if item.get('title', '') == magento_option), [])
        #     assigned_ptav_ids = set()
        #     for val in values:
        #         title_sku = {"title": val.get('title',""), "sku": val.get('sku',"")}; ir_log = True
        #         for ptav in self.filtered(lambda p: p.id not in assigned_ptav_ids):
        #             o_mov = json.loads(ptav.magento_option_value or "{}"); o_mov.pop('price',None); o_mov = json.dumps(o_mov)
        #             m_mov =  json.dumps(title_sku)
        #             o_sku_title = ptav.variant_suffix or "boş" + ptav.name or "boş"
        #             m_sku_title = title_sku['sku'] + title_sku['title']
        #             query = {o_mov:m_mov, o_sku_title: m_sku_title}
        #             _logger.warning(f"query: {query}")
        #             if any(fuzz.partial_ratio(key, value) > 95 for key, value in query.items()):
        #                 ptav.magento_option_value = json.dumps(title_sku | {"price": val.get('price', 0)}) # burda json.dumps kaldırılması gerekebilir.
        #                 assigned_ptav_ids.add(ptav.id); ir_log = False; break
        #         if ir_log:
        #             if self.sudo().env['ir.logging'].search([('name', '=', 'magento_ptav_title'), ('line','=', sku),('message', 'ilike', title_sku)]):
        #                 continue
        #             ir_data["message"].append(title_sku)
        #     if ir_data['message'] or not values:
        #         self[0].sudo().env['ir.logging'].magento_ir_logging(ir_data, email=False)
        # tüm ptav de magento_option_value boş olanları price 0 ve log not düşülmelidir.