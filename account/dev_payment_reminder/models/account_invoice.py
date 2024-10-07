# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from datetime import datetime
from datetime import timedelta
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)
from lxml import etree
from odoo.tools.safe_eval import safe_eval

class AccountMove(models.Model):
    _inherit = "account.move"

    # reminder_template = fields.Many2one('mail.template', string='Email Template', domain=[('model', '=', 'res.partner')],  tracking=True)
    reminder_template = fields.Many2one('payment.reminder.config', string='Email Template', tracking=True)
    reminder_state = fields.Boolean(string="Reminder Status", default=True, tracking=True)
    is_reminder_sent = fields.Boolean(string="Reminder Mail", default=False, tracking=True)

    @api.onchange('reminder_template')
    def _onchange_reminder_template(self):
        for move in self:
            move.is_reminder_sent = False

    # paid -> reminder_state False
    # CRON Auto
    def send_payment_reminder(self):
        c_date = datetime.now().date()
        for reminder in self.env['payment.reminder.config'].search([('template_id','!=', False), ('active','=',True)]):
            date = c_date - timedelta(days=reminder.day) # day = [10, 20, 30, 40]
            invoice_ids = self.env['account.move'].search([('move_type', '=', 'out_invoice'),
                                                           ('invoice_date', '=', date),
                                                           ('state', '=', 'posted'),
                                                           ('payment_state', '!=', 'paid'),
                                                           ('reminder_state', '=', True)
                                                           ])

            for inv in invoice_ids:
                # örn: manuel bir faturaya day 30 atandı. ama tarihi 9 gün geçmiş ertesi gün 10 olacağı için 10,20,30 gün mailleri gitmemesi için.
                if inv.reminder_template and inv.reminder_template.day >= reminder.day:
                    continue
                if not inv.invoice_payment_term_id:
                    pass # sor burayı continue olabilir misal
                domain = safe_eval(reminder.filter_domain)
                if (domain and inv.filtered_domain(domain)) or not domain:
                    inv.with_context(force_send=True).message_post_with_template(
                        reminder.template_id.id, email_layout_xmlid='mail.mail_notification_paynow')
                    inv.write({'reminder_template': reminder, 'is_reminder_sent': True})

    # manuel tree server action
    def send_payment_reminder_manuel(self):
        for mov in self:
            if not mov.is_reminder_sent and mov.reminder_template and mov.reminder_template.template_id:
                template_id = mov.reminder_template.template_id
                mov.with_context(force_send=True).message_post_with_template(template_id.id, email_layout_xmlid='mail.mail_notification_paynow')
                mov.write({'is_reminder_sent': True})

    # https://www.odoo.com/cs_CZ/forum/pomoc-1/odoo14-hiding-server-action-button-based-on-menu-page-190190
    # burası reminder modülün xml ninde context parametre gönderdik ve server action sadece remider gözğkmesini sağladık.
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        reminder_button_id = self.env.ref('dev_payment_reminder.action_dev_reminder').id or False
        reminder_server_action = self._context.get('reminder_server_action', False)
        if not reminder_server_action and view_type == 'tree':
            for button in res.get('toolbar', {}).get('action', []):
                if reminder_button_id and button['id'] == reminder_button_id:
                    res['toolbar']['action'].remove(button)
        return res

    def reminder_tag(self, payment_term):
        template_list = []
        if 'vorkasse' in payment_term:
            template_list = ['1']
        elif 'abschlag 50 % anzahlung' in payment_term \
                or '25 % anzahlung / 75 % nach enhalt der ware' in payment_term \
                or '70 % anzahlung / 30 % nach enhalt der ware' in payment_term:
            if inv.line_ids.sale_line_ids.order_id.invoice_status == 'invoiced':  # Fully invoiced
                template_list = ['1', '2', '3', '4']
            else:  # birinci fatura
                template_list = ['1']
        elif 'muster' in payment_term:
            template_list = ['1', '2', '3', '4']
        elif 'rechnung' in payment_term:
            template_list = ['1', '2', '3', '4']
        else:
            template_list = ['1']

        return template_list

    reminder_compute = fields.Boolean(compute="_compute_reminder_compute")
    def _compute_reminder_compute(self):
        ten_days_ago = fields.Date.today() - timedelta(days=9)
        for mov in self:
            if mov.move_type == 'out_invoice' and mov.state == 'posted' and \
                    mov.payment_state in ('not_paid', 'partial') and \
                    mov.invoice_date < ten_days_ago:
                mov.reminder_compute = True
            else:
                mov.reminder_compute = False
