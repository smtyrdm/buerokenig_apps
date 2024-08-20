# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'DIN 5008 - Purchase',
    'category': 'Accounting/Localizations',
    'depends': [
        'l10n_din5008',
        'purchase',
    ],
    "data": [
        "views/external_layout_din5008_inherit.xml",
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
