from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    week_date = fields.Char(string=_("Delivery Date"), compute="_onchange_date_planned")

    sale_delivery_note = fields.Html(string=_("Sale Delivery Note"), compute="_compute_sale_delivery_note")
    sale_week = fields.Char(string=_("Delivery Date"), compute="_compute_sale_delivery_note")

    def _compute_sale_delivery_note(self):
        for rec in self:
            for line in rec.order_line:
                date = line.sale_order_id.commitment_date
                incoterm = line.sale_order_id.incoterm

                sale_delivery_note = ""
                if date:
                    week_number = date.strftime('%V')
                    year = date.strftime('%Y')
                    # week_date alanını güncelleyin
                    sale_delivery_note += \
                        _("<strong>Sale Delivery Date: </strong>") + f"{week_number}. KW / {year} <br>"
                    rec.sale_week = f"{week_number}. KW / {year}"
                else:
                    rec.sale_week = False
                if incoterm:
                    sale_delivery_note += "<strong>Incoterm: </strong>" + f"{incoterm.name}" + "<br>"
                if hasattr(line.sale_order_id, 'delivery_note') and line.sale_order_id.delivery_note:
                    sale_delivery_note += "<strong>Delivery Note: </strong>" + f"{line.sale_order_id.delivery_note}"
                rec.sale_delivery_note = sale_delivery_note

    @api.onchange('date_planned')
    def _onchange_date_planned(self):
        for rec in self:
            if rec.date_planned:
                week_number = rec.date_planned.strftime('%V')
                year = rec.date_planned.strftime('%Y')
                # week_date alanını güncelleyin
                rec.week_date = f"{week_number}. KW / {year}"
            else:
                rec.week_date = False

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    week_date = fields.Char(string=_("Delivery Date"), compute="_onchange_date_planned")

    @api.onchange('date_planned')
    def _onchange_date_planned(self):
        for rec in self:
            if rec.date_planned:

                week_number = rec.date_planned.strftime('%V')
                year = rec.date_planned.strftime('%Y')
                # week_date alanını güncelleyin
                rec.week_date = f"{week_number}. KW / {year}"
            else:
                rec.week_date = False