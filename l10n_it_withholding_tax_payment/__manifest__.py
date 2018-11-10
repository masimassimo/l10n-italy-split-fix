# Copyright 2015 Alessandro Camilli (<http://www.openforce.it>)
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Italian Withholding Tax Payment',
    'version': '12.0.1.0.0',
    'category': 'Account',
    'author': 'Openforce, Odoo Italia Network, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-italy/',
    'license': 'AGPL-3',
    "depends": ['account',
                'l10n_it_withholding_tax'],
    "data": [
        'views/withholding_tax.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'wizard/create_move_payment_view.xml',
        'security/security.xml',
    ],
    "active": False,
    "installable": True
}
