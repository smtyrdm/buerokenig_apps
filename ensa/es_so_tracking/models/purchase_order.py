from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    is_purchase_sent = fields.Boolean(default=False, tracking=True)

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        result = super(PurchaseOrder, self).message_post(**kwargs)
        if self.env.context.get('mark_rfq_as_sent'):
            self.write({'is_purchase_sent': True})
        return result

    def button_cancel(self):
        self.write({'is_purchase_sent': False})
        return super(PurchaseOrder, self).button_cancel()

    def button_confirm(self):
        self.write({'is_purchase_sent': False})
        return super(PurchaseOrder, self).button_confirm()

