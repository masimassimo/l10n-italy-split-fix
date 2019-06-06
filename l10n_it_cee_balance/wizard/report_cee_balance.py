# Author(s): Alessandro Camilli (alessandrocamilli@openforce.it)
# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from openerp import models, fields, api
from openerp.exceptions import Warning
from odoo.tools import pycompat


class ReportCeeBalanceWizard(models.TransientModel):
    _name = "report.cee.balance.wizard"

    report = fields.Selection(
        [('profit_loss', 'Profit & Loss'),
         ('balance_sheet', 'Balance Sheet')],
        default = 'profit_loss'
        )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    fy_start_date = fields.Date(compute='_compute_fy_start_date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='all')
    hierarchy_on = fields.Selection(
        [('computed', 'Computed Accounts'),
         ('relation', 'Child Accounts'),
         ('none', 'No hierarchy')],
        string='Hierarchy On',
        required=True,
        default='computed',
        help="""Computed Accounts: Use when the account group have codes
        that represent prefixes of the actual accounts.\n
        Child Accounts: Use when your account groups are hierarchical.\n
        No hierarchy: Use to display just the accounts, without any grouping.
        """,
    )
    limit_hierarchy_level = fields.Boolean('Limit hierarchy levels')
    show_hierarchy_level = fields.Integer('Hierarchy Levels to display',
                                          default=1)
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    hide_account_at_0 = fields.Boolean(
        string='Hide accounts at 0', default=True,
        help='When this option is enabled, the trial balance will '
             'not display accounts that have initial balance = '
             'debit = credit = end balance = 0',
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    show_partner_details = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True,
        string='Not only one unaffected earnings account'
    )

    foreign_currency = fields.Boolean(
        string='Show foreign currency',
        help='Display foreign currency for move lines, unless '
             'account currency is not setup through chart of accounts '
             'will display initial and final balance in that currency.'
    )

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Handle company change."""
        account_type = self.env.ref('account.data_unaffected_earnings')
        count = self.env['account.account'].search_count(
            [
                ('user_type_id', '=', account_type.id),
                ('company_id', '=', self.company_id.id)
            ])
        self.not_only_one_unaffected_earnings_account = count != 1

    @api.depends('date_from')
    def _compute_fy_start_date(self):
        for wiz in self.filtered('date_from'):
            date = fields.Datetime.from_string(wiz.date_from)
            res = self.company_id.compute_fiscalyear_dates(date)
            wiz.fy_start_date = wiz.date_from

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.onchange('receivable_accounts_only', 'payable_accounts_only')
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = []
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [('internal_type', 'in', ('receivable', 'payable'))]
            elif self.receivable_accounts_only:
                domain += [('internal_type', '=', 'receivable')]
            elif self.payable_accounts_only:
                domain += [('internal_type', '=', 'payable')]
            self.account_ids = self.env['account.account'].search(domain)
        else:
            self.account_ids = None

    @api.onchange('show_partner_details')
    def onchange_show_partner_details(self):
        """Handle partners change."""
        if self.show_partner_details:
            self.receivable_accounts_only = self.payable_accounts_only = True
        else:
            self.receivable_accounts_only = self.payable_accounts_only = False

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_it_cee_balance.action_cee_balance_report_html')
        action_data = action.read()[0]
        context1 = action_data.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report_cee_balance_report']
        report = model.create(self._prepare_report_cee_balance_report())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        action_data['context'] = context1
        return action_data

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_cee_balance_report']
        report = model.create(self._prepare_report_cee_balance_report())
        report.compute_data_for_report()
        return report.print_report(report_type)

    def _prepare_report_cee_balance_report(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': self.hierarchy_on,
            'limit_hierarchy_level': self.limit_hierarchy_level,
            'show_hierarchy_level': self.show_hierarchy_level,
            'show_partner_details': self.show_partner_details,
        }
