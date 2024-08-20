from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval  # python_code
from datetime import datetime
#from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
import ast
from odoo.tools import is_html_empty


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    delivery_note = fields.Html(string='Delivery Note', readonly=False, compute="_compute_partner_lang")
    #dynamic_delivery_note = fields.Html(string='Delivery Note 1', related='incoterm.note')

    @api.onchange('incoterm', 'amount_total', 'partner_id', 'order_line')
    def onchange_delivery_note(self):
        try:
            python_code = self.incoterm.python_code
            if self.incoterm and python_code:
                model = self
                safe_eval(python_code.strip(), {'self': model}, mode="exec", nocopy=True)
            else:
                self.delivery_note = '' # dynamic_delivery_note gelebilir.
        except Exception as error:
            # self.payment_term_note2 = str(error)
            raise models.ValidationError("Delivery Code Hatalı %s" % str(error))
        
    @api.depends('partner_id.lang')
    def _compute_partner_lang(self):
        for rec in self:
            rec.onchange_delivery_note()

    @api.constrains('state')
    def incoterm_constrains_state(self):
        for rec in self:
            rec.onchange_delivery_note()