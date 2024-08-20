# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

import json
from odoo.tools.safe_eval import safe_eval

class AccountMove(models.Model):
    _inherit = 'account.move'

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
            # json_data = { 'en_US':{'1':'icerik','2':'icerik'}, 'de_DE':{}, 'tr_TR':{} }
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


    @api.onchange('invoice_payment_term_id', 'partner_id')
    def const_invoice_payment_term_id(self):
        if self.partner_id.lang:
            _logger.warning("const_invoice_payment_term_id ============ %s", self.invoice_payment_term_id)
            new_template_ids = self.template_ids
            if self.invoice_payment_term_id:
                terms = self.env['term.condition'].search([
                    ('active_model', '=', 'account.move'),
                    ('filter_domain', 'ilike', self.invoice_payment_term_id.name)]).sorted('sequence')
                for term in terms:
                    domain = safe_eval(term.filter_domain)
                    if domain and self.filtered_domain(domain):
                        new_template_ids |= terms
            if new_template_ids:
                for term in new_template_ids.sorted('sequence'):
                    domain = safe_eval(term.filter_domain)
                    if domain and not self.filtered_domain(domain):
                        new_template_ids = new_template_ids - term
                self.template_ids = new_template_ids
                self.onchange_template_id()
            else:
                terms_ids = self.env['term.condition']
                terms = self.env['term.condition'].search(
                    [('active_model', '=', 'account.move'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
                for term in terms:
                    domain = safe_eval(term.filter_domain)
                    if domain and self.filtered_domain(domain):
                        terms_ids |= term
                self.template_ids = terms_ids
                self.onchange_template_id()

    @api.depends('move_type')  # burda depends olduğundunda new_id origin veriyor. odoo 15 de onchange oluyır.
    def _compute_product_id_domain(self):
        _logger.warning("_compute_product_id_domain ====================")
        for rec in self:
            terms_ids = self.env['term.condition']
            terms = self.env['term.condition'].search(
                [('active_model', '=', 'account.move'), ('filter_domain', '!=', False)]).sorted('sequence')
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


    @api.constrains('move_type')
    def _constrains_move_type(self):
        _logger.warning("_constrains_move_type ================ %s", self.move_type)
        new_template_ids = self.template_ids.sorted('sequence')
        if new_template_ids:
            # mevcutlar yeni duruma göre silinecek.
            for term in new_template_ids:
                domain = safe_eval(term.filter_domain)
                if domain and not self.filtered_domain(domain):
                    new_template_ids = new_template_ids - term

            # default değerler new_template_ids eklenecek
            terms_ids = self.env['term.condition']
            terms = self.env['term.condition'].search(
                [('active_model', '=', 'account.move'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
            for term in terms:
                domain = safe_eval(term.filter_domain)
                if domain and self.filtered_domain(domain):
                    terms_ids |= term
            new_template_ids |= terms_ids

            self.template_ids = new_template_ids
            self.onchange_template_id()
        else: # template_ids boşsa direk defauşt değerler
            terms_ids = self.env['term.condition']
            terms = self.env['term.condition'].search(
                [('active_model', '=', 'account.move'), ('filter_domain', '!=', False), ('default','=',True)]).sorted('sequence')
            for term in terms:
                domain = safe_eval(term.filter_domain)
                if domain and self.filtered_domain(domain):
                    terms_ids |= term
            self.template_ids = terms_ids
            self.onchange_template_id()


    def button_reflesh_terms_conditions(self):
        self.json_field = False
        self.onchange_template_id()
