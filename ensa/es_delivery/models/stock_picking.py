from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    week_date = fields.Char(string=_("Scheduled Date"), compute="_onchange_date_planned")

    sale_delivery_date = fields.Datetime(string=_("Sale Delivery Date"), related="sale_id.commitment_date")

    @api.depends('sale_delivery_date')
    def _onchange_date_planned(self):
        for rec in self:
            if rec.sale_delivery_date:
                week_number = rec.sale_delivery_date.strftime('%V')
                year = rec.sale_delivery_date.strftime('%Y')
                # week_date alanını güncelleyin
                rec.week_date = f"{week_number}. KW / {year}"
            else:
                rec.week_date = False