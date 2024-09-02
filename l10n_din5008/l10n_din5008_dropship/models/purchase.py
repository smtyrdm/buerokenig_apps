from odoo import models, fields, _
from odoo.tools import format_date


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    l10n_din5008_phone = fields.Char(compute='_compute_l10n_din5008_phone', exportable=False)
    l10n_din5008_email = fields.Char(compute='_compute_l10n_din5008_email', exportable=False)
    def _compute_l10n_din5008_phone(self):
        for record in self:
            l10n_din5008_phone = ''
            if record.dest_address_id:
                if record.dest_address_id.type in ['delivery','contact']:
                    l10n_din5008_phone = record.dest_address_id.parent_id.phone if not record.dest_address_id.phone else ''
            record.l10n_din5008_phone = l10n_din5008_phone

    def _compute_l10n_din5008_email(self):
        for record in self:
            l10n_din5008_email = ''
            if record.dest_address_id:
                if record.dest_address_id.type in ['delivery','contact']:
                    l10n_din5008_email = record.dest_address_id.email or record.dest_address_id.parent_id.email or ""
            record.l10n_din5008_email = l10n_din5008_email

    def check_field_access_rights(self, operation, field_names):
        field_names = super().check_field_access_rights(operation, field_names)
        return [field_name for field_name in field_names if field_name not in {
            'l10n_din5008_phone',
            'l10n_din5008_email',
        }]
