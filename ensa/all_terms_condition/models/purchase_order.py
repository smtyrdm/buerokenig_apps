# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)
import json
import ast
from odoo.tools.safe_eval import safe_eval


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    template_ids_domain = fields.Char(string="Domain Filter", compute="_compute_template_ids_domain")

    # ondelete='restrict' -> term.condition kayıt silinmesini engeller.
    template_ids = fields.Many2many('term.condition', string='Note Terms', ondelete='restrict',
                                    store=True,
                                    readonly=False,
                                    compute="_compute_template_ids",
                                    default=lambda self: self._default_term_conditions(), )

    sale_term = fields.Html(string='Term')

    @api.model
    def _default_term_conditions(self):
        default_conditions = self.env['term.condition'].search([
            ('active_model', '=', 'purchase.order'),
            ('filter_domain', '!=', False),
            ('default','=', True)]).sorted('sequence')
        terms_to = []
        for term in default_conditions:
            domain = safe_eval(term.filter_domain)
            if domain and self.filtered_domain(domain):
                terms_to.append(term.id)
        #return default_conditions.ids
        _logger.warning("=================== _default_term_conditions %s",terms_to )
        return terms_to or []

    def _onchange_template_ids(self):
        for rec in self:
            terms_to = []
            if rec.template_ids:
                for term in rec.template_ids.sorted('sequence'):
                    domain = safe_eval(term.filter_domain)
                    if domain and rec.filtered_domain(domain):
                        terms_to.append(term.id)
            return terms_to or []

    @api.depends('partner_id.lang')
    def _compute_template_ids(self):
        for rec in self:
            terms_to = rec._onchange_template_ids()
            rec.template_ids = [(6, 0, terms_to)]
            rec._onchange_sale_term()

    @api.onchange('payment_term_id', 'partner_id', 'state')
    def _compute_template_ids_domain(self):
        for rec in self:
            terms_ids = self.env['term.condition']
            terms = self.env['term.condition'].search(
                [('active_model', '=', 'purchase.order'), ('filter_domain', '!=', False)]).sorted('sequence')
            for term in terms:
                domain = safe_eval(term.filter_domain)
                if domain and rec.filtered_domain(domain):
                    terms_ids |= term

            rec.template_ids_domain = json.dumps([('id', 'in', terms_ids.ids)]) if terms_ids else False

    @api.onchange('template_ids')
    def _onchange_sale_term(self):
        self.sale_term = '\n'.join(term.with_context({'lang': self.partner_id.lang}).template for term in self.template_ids.sorted('sequence') if term.template)

    @api.constrains('state')
    def constrains_payment_term(self):
        for rec in self:
            default = rec._default_term_conditions() # default term -> filter uyumlu
            records = rec._onchange_template_ids() # kayıtlı term -> filter uyumlu
            rec.template_ids = [(6, 0, default + records)]
            rec._onchange_sale_term()

    def button_reflesh_terms_conditions(self):
        self._compute_template_ids()

    @api.onchange('payment_term_id','partner_id') #
    def onchange_term_payment_term(self):
        for rec in self:
            rec.constrains_payment_term()
