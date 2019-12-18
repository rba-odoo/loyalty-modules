# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Loyalty Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: loyalty',
    'version': '1.0',
    'author': 'leelapriskila',
    'description': """Loyalty Payment Acquirer""",
    'depends': ['payment'],
    'application': True,
    'data': [
        'views/payment_views.xml',
        'views/payment_loyalty_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
