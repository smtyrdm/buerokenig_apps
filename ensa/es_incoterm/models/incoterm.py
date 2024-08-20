from odoo import api, fields, models, _
from odoo.tools import format_date

import logging
_logger = logging.getLogger(__name__)


class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    DEFAULT_PYTHON_CODE = """# Available variables:
    #  - env: Odoo Environment on which the action is triggered
    #  - model: Odoo Model of the record on which the action is triggered; is a void recordset
    #  - record: record on which the action is triggered; may be void
    #  - records: recordset of all records on which the action is triggered in multi-mode; may be void
    #  - time, datetime, dateutil, timezone: useful Python libraries
    #  - float_compare: Odoo function to compare floats based on specific precisions
    #  - log: log(message, level='info'): logging function to record debug information in ir.logging table
    #  - UserError: Warning Exception to use with raise
    #  - Command: x2Many commands namespace
    #  - for rec in self:
    #       rec['delivery_note'] = ''
    #       if rec._name == "sale.order":
    #           if rec.state == "sale":
    #               if rec.partner_id.lang == 'de_DE':
    #                   rec['delivery_note'] = 'Die Lieferung erfolgt frei Verwendungsstelle.'
    #               else:
    #                    rec['delivery_note'] = 'Delivery is free to the point of use.'
    # To return an action, assign: action = {...}\n\n\n\n"""

    sequence = fields.Integer()
    python_code = fields.Text('Python code', default=DEFAULT_PYTHON_CODE)





