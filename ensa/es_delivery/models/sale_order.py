from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import format_date
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    week_date = fields.Char(string=_("Delivery Date"), compute="_onchange_commitment_date")

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        for rec in self:
            if rec.commitment_date:
                week_number = rec.commitment_date.strftime('%V')
                year = rec.commitment_date.strftime('%Y')
                rec.week_date = f"{week_number}. KW / {year}"
            else:
                rec.week_date = False
    # Dropship address
    # SO ve PO oluşmuş fakat sonra SO teslim aderesi güncellenince PO da güncellenmek istenmiş.
    @api.onchange('partner_shipping_id')
    def _set_new_address(self):
        purchase_ids = self.env['purchase.order'].search([('origin', 'ilike', self.name)])
        if purchase_ids:
            for purchase in purchase_ids:
                purchase.dest_address_id = self.partner_shipping_id
        dropship_ids = self.env['stock.picking'].search([('sale_id.name', 'ilike', self.name)])
        if dropship_ids:
            for dropship in dropship_ids:
                dropship.move_lines[0].partner_id = self.partner_shipping_id.id



