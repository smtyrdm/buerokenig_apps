# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

import json
from odoo.tools.safe_eval import safe_eval

ADDRESS_FIELDS = ('payment_term_id','name')
class SaleOrder(models.Model):
    _inherit = 'sale.order'



    # @api.onchange('payment_term_id')
    # def enginn(self):
    #     global ADDRESS_FIELDS
    #     _logger.warning("====================== ADDRESS_FIELDS enginn 11  %s", ADDRESS_FIELDS)
    #     ADDRESS_FIELDS = ('state',)
    #
    #     _logger.warning("====================== ADDRESS_FIELDS 11  %s", ADDRESS_FIELDS)
    # @api.onchange('date_order')
    # def enginnw(self):
    #     global ADDRESS_FIELDS
    #     _logger.warning("====================== ADDRESS_FIELDS  enginnw 22%s", ADDRESS_FIELDS)

    #@api.onchange(*ADDRESS_FIELDS)

    payment_term_note = fields.Html(string='Term', translate=True)
    json_payment = fields.Char(store=True)

    # ondelete='restrict' -> term.condition kayıt silinmesini engeller.
    template_ids = fields.Many2many('term.condition', string='Note Terms', ondelete='restrict')
    template_ids_boolean = fields.Boolean(store=False, default=False)
    template_ids_domain = fields.Char(
        compute="_compute_product_id_domain",
        readonly=True,
        store=False,
    )
    partner_id_lang = fields.Char()

    sale_term = fields.Html(string='Term', translate=True)
    json_field = fields.Char(string='JSON Field', store=True)

    # burda depends olduğundunda new_id origin veriyor. odoo 15 de onchange oluyır.
    def _compute_product_id_domain(self):
        _logger.warning("_compute_product_id_domain ====================")
        for rec in self:
            terms_ids = self.env['term.condition']
            terms = self.env['term.condition'].search(
                [('active_model', '=', 'sale.order'), ('filter_domain', '!=', False)]).sorted('sequence')
            for term in terms:
                domain = safe_eval(term.filter_domain)
                if domain and rec.filtered_domain(domain):
                    terms_ids |= term
            rec.template_ids_domain = json.dumps([('id', 'in', terms_ids.ids)]) if terms_ids else False

            if not rec.partner_id_lang:
                rec.partner_id_lang = rec.partner_id.lang
            elif rec.partner_id_lang != rec.partner_id.lang:
                rec.partner_id_lang = rec.partner_id.lang
                self.onchange_template_id()

    # template_ids_domain -> web_domain_field modülü ile çalışıyor.
    @api.onchange('template_ids','partner_id')
    def onchange_template_id(self):
        _logger.warning("onchange_template_id =================")
        if self.partner_id.lang:
            languages = self.env['res.lang'].search([('active', '=', 'true')])
            if self.json_field:
                json_data = json.loads(self.json_field) # Varolan JSON verilerini çözümle
            else:
                json_data = {}
                for lang in languages:
                    json_data[lang.code]={}
            for lang in languages:
                if not json_data.get(lang.code):
                    json_data[lang.code] = {}
                all_keys = list(json_data[lang.code].keys())
                for rec in self.template_ids.sorted('sequence'):
                    if str(rec._origin.id) not in all_keys:
                        template = rec.with_context({'lang': lang.code}).template # self.partner_id.lang
                        if template:
                            json_data[lang.code][str(rec._origin.id)] = template
                        else:
                            json_data[lang.code][str(rec._origin.id)] = rec.template
                    if str(rec._origin.id) in all_keys:
                        all_keys.remove(str(rec._origin.id))

                for key in all_keys:
                    if key in json_data[lang.code]:
                        del json_data[lang.code][key]

            all_vals = json_data[self.partner_id.lang].values()  # tüm values'leri al
            self.sale_term = '\n'.join(all_vals)
            # Güncellenmiş JSON verilerini string formatına çevir
            updated_json_data = json.dumps(json_data)
            # Kaydın 'json_data' alanını güncelle
            self.json_field = updated_json_data




        # if self.partner_id.lang:
        #     new_template_ids = self.template_ids
        #     # if self.payment_term_id:
        #     #     terms = self.env['term.condition'].search([
        #     #         ('active_model', '=', 'sale.order'),
        #     #         ('filter_domain', 'ilike', self.payment_term_id.name)]).sorted('sequence')
        #     #     for term in terms:
        #     #         domain = safe_eval(term.filter_domain)
        #     #         if domain and self.filtered_domain(domain):
        #     #             self.template_ids |= terms
        #     if self.template_ids:
        #         for term in self.template_ids.sorted('sequence'):
        #             domain = safe_eval(term.filter_domain)
        #             if domain and not self.filtered_domain(domain):
        #                 self.template_ids = self.template_ids - term
        #         #self.template_ids = new_template_ids
        #         self.onchange_template_id()
        #     else:
        #         terms_ids = self.env['term.condition']
        #         terms = self.env['term.condition'].search(
        #             [('active_model', '=', 'sale.order'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
        #         for term in terms:
        #             domain = safe_eval(term.filter_domain)
        #             if domain and self.filtered_domain(domain):
        #                 terms_ids |= term
        #         self.template_ids = terms_ids
        #         self.onchange_template_id()

    @api.constrains('state','payment_term_id')
    def _constrains_state(self):
        new_template_ids = self.template_ids.sorted('sequence')

        # if new_template_ids:
        # mevcutlar yeni duruma göre silinecek.
        for term in new_template_ids:
            domain = safe_eval(term.filter_domain)
            if domain and not self.filtered_domain(domain):
                new_template_ids = new_template_ids - term
        # else:
            # default değerler new_template_ids eklenecek
        terms_ids = self.env['term.condition']
        terms = self.env['term.condition'].search(
            [('active_model', '=', 'sale.order'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
        for term in terms:
            domain = safe_eval(term.filter_domain)
            if domain and self.filtered_domain(domain):
                terms_ids |= term
        new_template_ids |= terms_ids

        self.template_ids = new_template_ids
        self.onchange_template_id()
        self._compute_product_id_domain()
        # else: # template_ids boşsa direk defauşt değerler
        #     terms_ids = self.env['term.condition']
        #     terms = self.env['term.condition'].search(
        #         [('active_model', '=', 'sale.order'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
        #     for term in terms:
        #         domain = safe_eval(term.filter_domain)
        #         if domain and self.filtered_domain(domain):
        #             terms_ids |= term
        #     self.template_ids = terms_ids
        #     self.onchange_template_id()

            # if rec._origin.state and rec.state != rec._origin.state:
            #     _logger.warning("girfiiiiii")
            #     rec.const_payment_term_id()
            #self.const_payment_term_id()

            #rec.template_ids = terms_ids.filtered(lambda l: l.default) if terms_ids else False
            #rec.onchange_template_id()


    def button_reflesh_terms_conditions(self):
        self.json_field = False
        self.onchange_template_id()












        # terms = self.env['term.condition'].search([
        #     ('active_model', '=', 'sale.order'),
        #     ('default','=', False),
        #     ('filter_domain', 'ilike', 'payment_term_id'),
        #     ('filter_domain', '!=', False)])
        # terms_ids = self.env['term.condition']
        # new_template_ids = self.template_ids - terms
        # if self.payment_term_id:
        #     for term in new_template_ids:
        #         domain = safe_eval(term.filter_domain)
        #         if domain and self.filtered_domain(domain):
        #             #if term.id not in self.template_ids.ids:
        #             terms_ids |= term
        #     if terms_ids:
        #         self.template_ids = terms_ids
        # else:
        #     self.template_ids = new_template_ids

    # @api.model
    # def _get_template_domain(self):
    #     list2 =[]
    #     terms = self.env['term.condition'].search(
    #         [('active_model', '=', 'sale.order'), ('filter_domain', '!=', False)]).sorted('sequence')
    #     for term in terms:
    #         domain = safe_eval(term.filter_domain)
    #         if domain and self.filtered_domain(domain):
    #             list2.append(term.id)
    #     _logger.warning("list2 ========= list2 %s",list(list2))
    #     return [('id', 'in', list(list2))]

    # def _get_default_template_ids(self):
    #     terms = self.env['term.condition'].search([('active_model', '=', 'sale.order'), ('filter_domain', '!=', False), ('default', '=', True)]).sorted('sequence')
    #     terms_ids = self.env['term.condition']
    #     for term in terms:
    #         domain = safe_eval(term.filter_domain)
    #         if domain and self.filtered_domain(domain):
    #             terms_ids |= term
    #     _logger.warning("girgiiiiii ?=============  terms_ids %s", terms_ids)
    #     if terms_ids:
    #         return terms_ids
    #     else:
    #         return None

    # def write_template_ids(self,vals):
    #     _logger.warning("engin write_template_ids")
    #     model = self._inherit[0] if isinstance(self._inherit, list) else self._inherit
    #     terms = self.env['term.condition'].search(
    #         [('active_model', '=', model), ('filter_domain', '!=', False), ('default', '=', True)]).sorted('sequence')
    #     has_entered_if = False
    #     for term in terms:
    #         domain = safe_eval(term.filter_domain)
    #         if domain and self.filtered_domain(domain):
    #             # for item in domain:
    #             #     if isinstance(item, list):
    #             #         field, operator, value = item
    #             #         if field in vals:
    #             #             # İlk kez koşula girdiyse template_ids'i temizle
    #             #             if not has_entered_if:
    #             #                 _logger.warning("engin 7")
    #             #                 self.template_ids = False
    #             #                 has_entered_if = True
    #             #             _logger.warning("engin 11")
    #             self.template_ids |=  term
    #             #self.template_ids = [(4, term.id, 0)]
    #
    #

    #
    #
    #

    # if self._origin.id:
    # template = self.template_ids.mapped('template')
    # self.sale_term = '\n'.join(template)
    # languages = self.env['res.lang'].search([('active', '=', 'true')])
    # self.sale_term = ""
    # for rec in self.template_ids:
    #     self.sale_term += f"{rec.template}\n"
    #     for lang in languages: #['en_US', 'de_DE', 'tr_TR']
    #         translated = rec.with_context({'lang': lang.code}).template #.mapped('template')  # ['','']
    #         _logger.warning("translated %s", translated)
    #         if translated:
    #             sale_term = self.with_context({'lang': lang.code}).sale_term
    #             _logger.warning("sale_term %s", sale_term)

    # existing_trans = self.env['ir.translation'].search([('name', '=', 'sale.order,sale_term'),
    #                                                     ('res_id', '=', self._origin.id),
    #                                                     ('lang', '=', lang.code)
    #                                                     ])
    # _logger.warning("222222")
    # _logger.warning("222222 %s", existing_trans)
    #
    #
    # data = {
    #     'type': 'model_terms',
    #     'name': 'sale.order,sale_term',
    #     'lang': lang.code,
    #     'res_id': self._origin.id,
    #     'src': self._origin.sale_term,
    #     'value': sale_term,
    #     'state': 'translated'
    # }
    # if not existing_trans:
    #     self.env['ir.translation'].create(data)
    # else:
    #     existing_trans.unlink()
    #     self.env['ir.translation'].create(data)

    # def create_or_update_translations(self, model_name, lang_code, res_id, src, value):
    #     data = {
    #         'type': 'model',
    #         'name': model_name,
    #         'lang': lang_code,
    #         'res_id': res_id,
    #         'src': src,
    #         'value': value,
    #         'state': 'inprogress',
    #     }
    #     existing_trans = self.env['ir.translation'].search([('name', '=', model_name),
    #                                                         ('res_id', '=', res_id),
    #                                                         ('lang', '=', lang_code)])
    #     if not existing_trans:
    #         self.env['ir.translation'].create(data)
    #     else:
    #         existing_trans.unlink()
    #         self.env['ir.translation'].create(data)
    #

    # terms = []
    # for rec in self.template_ids.sorted('sequence'):
    #     terms.append(rec.template)
    # self.sale_term = '\n'.join(terms)

    # translations = {
    #     'en_US': 'deneme1',
    #     'de_DE': 'deneme2',
    #     'tr_TR': 'deneme3',
    # }
    # for lang, translation in translations.items():
    #     _logger.warning("res_id =============== %s", self.id)
    #     _logger.warning("res_id =============== %s", self.id)
    #     existing_translation = self.env['ir.translation'].search([
    #         ('name', '=', 'sale.order,sale_term'),
    #         ('res_id', '=', _origin.id),
    #         ('lang', '=', lang)
    #     ])
    #     _logger.warning("existing_translation %s", existing_translation.value)

    # sale_term_de = self.with_context(lang=lang_code)
    # sale_term_de.sale_term = translation
    # self.write({'sale_term': translation})
    # self.with_context(lang=lang_code).write({'sale_term': translation})

    # user_lang = self.env.user.lang
    # _logger.warning("engin11 user_lang %s", user_lang)
    # languages = self.env['res.lang'].search([('active', '=', True)]).mapped('code')
    # _logger.warning("languages %s", languages)
    # for lang in languages: #  ['en_US', 'de_DE', 'tr_TR']
    #     translated = self.template_ids.with_context({'lang': lang}).mapped('name') # ['','']
    #     sale_term = '\n'.join(translated)
    #     #self.with_context({'lang': lang}).write({'sale_term': terms})
    #     self.sudo().with_context({'lang': lang}).sale_term = sale_term

    # sale_term = self.with_context({'lang': lang})
    # if sale_term:
    #     self.with_context({'lang': lang}).write({'sale_term': terms})
    # else:
    #     self.with_context({'lang': lang}).create({'sale_term': terms})

    # 'name2' için çeviri zaten var mı kontrol et
    # existing_translation = self.env['ir.translation'].search([
    #     ('name', '=', 'sale.order,sale_term'),
    #     ('res_id', '=', self.id),
    #     ('lang', '=', lang)
    # ])
    # _logger.warning("existing_translation %s", existing_translation)
    # if existing_translation:
    #     _logger.warning("var")
    #     # Var olan çeviriyi güncelle
    #     existing_translation.write({'value': terms})
    # else:
    #     _logger.warning("yok")
    #
    #     # Yeni çeviri oluştur
    #     self.env['ir.translation'].create({
    #         'name': 'sale.order,sale_term',
    #         'res_id': self.id,
    #         'lang': lang,
    #         'type': 'model',
    #         'src': self.sale_term,
    #         'value': terms
    #     })

    # terms = []
    # for rec in self.template_ids.sorted('sequence'):
    #     for lang in languages:
    #         translated = rec.with_context({'lang': lang})
    # sale_term_translated = self.with_context({'lang': lang}).sale_term
    # translated_name = rec.with_context({'lang': lang}).name
    # self.with_context({'lang': lang}).write({'sale_term': translated.template})
    # self.with_context({'lang': lang}).write({'sale_term': sale_term_translated + '\n' +  translated.template})
    # {'name2': rec.name2 + '\n' + translated_name}
    #     terms.append(rec.template)
    # self.sale_term = '\n'.join(terms)

    # @api.onchange('template_id')
    # def onchange_template_id(self):
    #     self.sale_term = False
    #     for rec in self.template_id:
    #         self.sale_term += rec.template + '\n'
