from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for so in self:
            if so.user_id.name == "OdooBot":
                raise models.ValidationError("Change Salesperson OdooBot..")
        return res


    def action_quotation_send(self):
        self.ensure_one()
        res = super(SaleOrder, self).action_quotation_send()
        for so in self:
            if so.user_id.name == "OdooBot":
                raise models.ValidationError("Change Salesperson OdooBot..")
        return res