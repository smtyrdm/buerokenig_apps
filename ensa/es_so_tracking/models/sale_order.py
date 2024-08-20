from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit="sale.order"

    is_sale_sent  = fields.Boolean(default=False, copy=False, tracking=True)

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        result = super(SaleOrder, self).message_post(**kwargs)
        if self.env.context.get('mark_so_as_sent'):
            self.write({'is_sale_sent': True})
        return result

    def action_cancel(self):
        self.write({'is_sale_sent': False})
        return super(SaleOrder, self).action_cancel()

    def action_confirm(self):
        self.write({'is_sale_sent': False})
        return super(SaleOrder, self).action_confirm()

