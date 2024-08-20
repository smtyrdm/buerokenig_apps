from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval  # python_code
from datetime import datetime
#from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
import ast


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    delivery_note = fields.Html(string='Delivery Note', readonly=False, compute="_compute_delivery_note")


    def _compute_delivery_note(self):
        try:
            python_code = self.sale_id.incoterm.python_code
            if self.sale_id.incoterm and python_code:
                model = self
                safe_eval(python_code.strip(), {'self': model}, mode="exec", nocopy=True)
            else:
                self.delivery_note = ""
        except Exception as error:
            raise models.ValidationError("Delivery Code Hatalı %s" % str(error))




    # @api.depends('sale_id')
    # def onchange_delivery_note(self):
    #     try:
    #         python_code = self.incoterm.python_code
    #         #code_without_comments = '\n'.join(line for line in python_code.split('\n') if not line.strip().startswith('#'))
    #         if self.incoterm and python_code: # and code_without_comments:
    #             model = self
    #             safe_eval(python_code.strip(), {'self': model}, mode="exec", nocopy=True)
    #         else:
    #             self.delivery_note = ""
    #     except Exception as error:
    #         # self.payment_term_note2 = str(error)
    #         raise models.ValidationError("Delivery Code Hatalı %s" % str(error))
    #         #self.payment_note = ""
    # # burda partner_id.lang değiştiğinde partner ait tüm kayıtlarda bu fonksiyon çalışacak.
    # @api.depends('partner_id.lang')
    # def _compute_partner_lang(self):
    #     for rec in self:
    #         rec.onchange_delivery_note()
    #
    # @api.constrains('state')
    # def incoterm_constrains_state(self):
    #     for rec in self:
    #         rec.onchange_delivery_note()