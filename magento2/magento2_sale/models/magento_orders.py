import logging
from odoo import models, fields, exceptions, api, _

logger = logging.getLogger(__name__)
class SaleOrderMagento(models.Model):
    _inherit = 'sale.order'

    magento_id = fields.Char(string="Magento Id", store=True)
    magento_entity_id = fields.Char(string='Magento Order ID',store=True)
    magento = fields.Boolean(string="Magento", store=True, help="This order is created from magento.")
    magento_status = fields.Char(string="Magento status")
    magento_order_date = fields.Datetime(string="Magento Order Date")



    def magento_post_url(self):
        # https://tischkoenig.com.tr/tischkoenig-giris/sales/order/view/order_id/2252/
        ICPSudo = self.env['ir.config_parameter'].sudo()
        magento_admin_url = ICPSudo.get_param('magento2.magento_admin_url')
        order_url = f"https://{magento_admin_url}/sales/order/view/order_id/{self.magento_entity_id}/"
        if magento_admin_url and self.magento_entity_id:
            return {
                'type': 'ir.actions.act_url',
                'url': order_url,
                'target': 'new',  # Opens in a new tab
            }


    # def action_cancel(self):
    #     res = super(SaleOrderMagento, self).action_cancel()
    #     if self.magento:
    #         rec = self.env['shipment.shipment'].search([
    #             ('related_so', '=', self.id)
    #         ])
    #         if rec.id:
    #             rec.state = 'cancel'
    #     return res


class CustomerMagento(models.Model):
    _inherit = 'res.partner'
    magento = fields.Boolean(string="Magento", readonly=True, store=True, help="This customer is created from magento.")
    magento_id = fields.Char(string="Magento id", store=True)


class AccountInvoice(models.Model):
    _inherit = 'account.move'
    magento = fields.Boolean(string="Magento", readonly=True, store=True, compute="_compute_so_magento")
    magento_id = fields.Char(string="Magento Id", readonly=True, store=True)

    @api.depends('line_ids.sale_line_ids.order_id')
    def _compute_so_magento(self):
        for mov in self:
            so = mov.line_ids.sale_line_ids.order_id.filtered(lambda s: s.magento and s.state in ['sale','done'])
            mov.magento = True if so.magento else False
            mov.magento_id = so.mapped('magento_id') or ''
