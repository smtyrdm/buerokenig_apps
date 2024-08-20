# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.safe_eval import safe_eval
from ast import literal_eval


class TermCondition(models.Model):
    _name = 'term.condition'
    _description = 'Terms and Conditions'
    _order = 'sequence, filter_domain'

    name = fields.Char('Name', translate=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, auto_join=True, ondelete='cascade')
    # related_fields = fields.Many2many('ir.model.fields', string='Related Fields', domain="[('model_id', '=', model_id)]")
    model = fields.Char('Model Name', related='model_id.model')
    filter_domain = fields.Char(
        string="Apply On",
        default="[]",
        help="Find matching option by document values",
    )
    filter_field = fields.Char()
    # render_engine: HTML içeriğini işlemek
    # sanitize: HTML içeriğinin temizlenmesini (zararlı kodları filtreleme) devre dışı bırakır.
    template = fields.Html('Template', translate=True)
    #body_html = fields.Html('Body', render_engine='qweb', translate=True, sanitize=False)
    default = fields.Boolean('Default')

    active = fields.Boolean('Active', default=True)
    active_model = fields.Char('Active Model', readonly=True)
    sequence = fields.Integer(string='Sequence')

    @api.model
    def default_get(self, fields):
        vals = super(TermCondition, self).default_get(fields)
        active_model = self.env.context.get('active_model', False) or self.env.context.get('default_active_model', False)
        #self.env.context = dict(self.env.context)   self.env.context['model_id'] = model_id.id
        model_id = self.env['ir.model'].search([('model', '=', active_model)],limit=1)
        vals['model_id'] = model_id.id or False
        return vals
