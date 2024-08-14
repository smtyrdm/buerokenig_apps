
import logging
from odoo import models, fields, exceptions, _, api

logger = logging.getLogger(__name__)

class MagentoPayment(models.Model):
    _inherit = 'magento.account.payment'


    def find_magento_payment(self,i):
        # Payment Method
        method = i.get('payment', {}).get('method', '')
        payment = self.env['magento.account.payment'].search([('code', '=', method)], limit=1)
        if not payment or payment and not payment.payment_term_id:
            raise models.ValidationError(f"Account/Magento Payment | [{ i.get('payment', {})}] not!")
        payment_method = payment.payment_term_id

        return payment_method