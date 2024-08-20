from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_no = fields.Char(string="PO", readonly=True, tracking=True, compute="_compute_purchase_order_no")
    inv_no = fields.Char(string="IN", readonly=True, tracking=True, compute="_compute_inv_no")

    def _compute_purchase_order_no(self):
        for order in self:
            purchase_order_name = order._get_purchase_orders().mapped('name')
            order.purchase_order_no = ', '.join(purchase_order_name) if purchase_order_name else False

    def _compute_inv_no(self):
        for order in self:
            inv_name = order.invoice_ids.mapped('name')
            order.inv_no = ', '.join(inv_name) if inv_name else False

    is_sale_sent_selection = fields.Selection([
        ('true', '✓'),
        ('false', 'X'),
        ('warning', '(!)'),
    ], default="warning", compute="_compute_so_mail_sent")
    is_purchase_sent = fields.Selection([
        ('true', '✓'),
        ('false', 'X'),
        ('warning', '(!)'),
    ], default="warning", compute="_compute_po_mail_sent")
    is_move_sent = fields.Selection([
        ('true', '✓'),
        ('false', 'X'),
        ('warning', '(!)'),
    ], default="warning", compute="_compute_in_mail_sent")

    def _compute_so_mail_sent(self):
        for rec in self:
            rec.is_sale_sent_selection = 'true' if rec.is_sale_sent else 'false'

    def _compute_po_mail_sent(self):
        for rec in self:
            purchase = rec.order_line.purchase_line_ids.filtered(lambda l: l.state != 'cancel').mapped('order_id.is_purchase_sent') or [False]
            if len(purchase) > 1 and not all(purchase):
                rec.is_purchase_sent = 'warning'
            else:
                rec.is_purchase_sent = 'true' if all(purchase) else 'false'

    def _compute_in_mail_sent(self):
        for rec in self:
            move = rec.order_line.invoice_lines.filtered(lambda l: l.move_id.move_type == 'out_invoice').mapped('move_id.is_move_sent') or [False]
            if len(move) > 1 and not all(move):
                rec.is_move_sent = 'warning'
            else:
                rec.is_move_sent = 'true' if all(move) else 'false'

    picking_name = fields.Char(compute="_compute_picking_name")

    @api.depends('picking_ids')
    def _compute_picking_name(self):
        for rec in self:
            ds = rec.picking_ids.mapped('name')
            rec.picking_name = ', '.join(ds) if ds else False

    is_sent_control = fields.Boolean(compute="_compute_is_sent_control", store=True)
    sent_tracking = fields.Boolean(default=True, copy=False, tracking=True)

    @api.depends('is_sale_sent',
                 'state',
                 'order_line.purchase_line_ids.order_id.is_purchase_sent',
                 'order_line.invoice_lines.move_id.is_move_sent',
                 'order_line.invoice_lines.move_id.payment_state',
                 )
    def _compute_is_sent_control(self):
        for rec in self:
            is_move_sent = rec.order_line.invoice_lines.filtered(lambda l: l.move_id.move_type == 'out_invoice').mapped('move_id.is_move_sent') or [False]
            is_payment = rec.invoice_ids.mapped('payment_state')
            is_payment = all(pay == 'paid' for pay in is_payment) or False
            is_purchase_sent = rec.order_line.purchase_line_ids.filtered(lambda l: l.state != 'cancel').mapped('order_id.is_purchase_sent') or [False]
            if rec.state == 'cancel':
                rec.is_sent_control = True
                rec.sent_tracking = False
            elif rec.is_sale_sent and all(is_move_sent) and all(is_purchase_sent) and is_payment:
                rec.is_sent_control = True
                rec.sent_tracking = False
            else:
                rec.is_sent_control = False
                rec.sent_tracking = True
