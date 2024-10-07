# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields


class payment_reminder_confi(models.Model):
    _name = "payment.reminder.config"
    _description = "Payment Reminder Config"

    day = fields.Integer('Days', required="1")
    template_id = fields.Many2one('mail.template', string='Email Template', required="1", domain=[('model', '=', 'account.move')])
    # engin: 12.09.2024
    filter_domain = fields.Char(
        string="Apply On",
        default="[]",
        help="Find matching option by document values",
    )
    active = fields.Boolean('Active', default=True)

    # name_get yöntemini özelleştirme
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.day} days / {record.template_id.name}" if record.day and record.template_id else ''
            result.append((record.id, name))
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: