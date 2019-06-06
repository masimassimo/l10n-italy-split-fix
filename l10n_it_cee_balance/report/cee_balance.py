# Author(s): Alessandro Camilli (alessandrocamilli@openforce.it)
# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _

class ReportCeeBalanceReport(models.TransientModel):
    _name = 'report_cee_balance_report'
    _inherit = 'report_cee_balance_report_abstract'

    # Filters fields, used for data computation
    report = fields.Selection(
        [('profit_loss', 'Profit & Loss'),
         ('balance_sheet', 'Balance Sheet')],
        default = 'profit_loss'
        )
    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    fy_start_date = fields.Date()
    only_posted_moves = fields.Boolean()
    hide_account_at_0 = fields.Boolean()
    foreign_currency = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    filter_journal_ids = fields.Many2many(comodel_name='account.journal')
    show_partner_details = fields.Boolean()
    hierarchy_on = fields.Selection(
        [('computed', 'Computed Accounts'),
         ('relation', 'Child Accounts'),
         ('none', 'No hierarchy')],
        string='Hierarchy On',
        required=True,
        default='relation',
        help="""Computed Accounts: Use when the account group have codes
        that represent prefixes of the actual accounts.\n
        Child Accounts: Use when your account groups are hierarchical.\n
        No hierarchy: Use to display just the accounts, without any grouping.
        """,
    )
    limit_hierarchy_level = fields.Boolean('Limit hierarchy levels')
    show_hierarchy_level = fields.Integer('Hierarchy Levels to display',
                                          default=1)

    # Trial Balance Report Data fields,
    # used as base for compute the data reports
    trial_balance_id = fields.Many2one(
        comodel_name='report_trial_balance'
    )

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_cee_balance_report_account',
        inverse_name='report_id'
    )


class ReportCeeBalanceReportAccount(models.TransientModel):
    _name = 'report_cee_balance_report_account'
    _inherit = 'report_cee_balance_report_abstract'

    report_id = fields.Many2one(
        comodel_name='report_cee_balance_report',
        ondelete='cascade',
        index=True,
    )

    hide_line = fields.Boolean(compute='_compute_hide_line')
    # Data fields, used to keep link with real object
    # sequence = fields.Integer(index=True, default=1)
    sequence = fields.Char(index=True)
    level = fields.Integer(index=True, default=1)

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )
    account_group_cee_id = fields.Many2one(
        'account.group.cee',
        index=True
    )
    parent_cee_id = fields.Many2one(
        'account.group.cee',
        index=True
    )
    child_account_ids = fields.Char(
        string="Accounts")
    compute_account_ids = fields.Many2many(
        'account.account',
        string="Accounts", store=True)

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()

    currency_id = fields.Many2one('res.currency')
    initial_balance = fields.Float(digits=(16, 2))
    initial_balance_foreign_currency = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    period_balance = fields.Float(digits=(16, 2))
    final_balance = fields.Float(digits=(16, 2))
    final_balance_foreign_currency = fields.Float(digits=(16, 2))

    @api.multi
    def _compute_hide_line(self):
        for rec in self:
            report = rec.report_id
            rec.hide_line = False
            if report.hide_account_at_0 and (
                    not rec.initial_balance and
                    not rec.final_balance and
                    not rec.debit and
                    not rec.credit):
                rec.hide_line = True
            elif report.limit_hierarchy_level and \
                    rec.level > report.show_hierarchy_level:
                rec.hide_line = True


class ReportCeeBalanceReportCompute(models.TransientModel):
    _inherit = 'report_cee_balance_report'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.cee_balance_report_xlsx'
        else:
            report_name = 'l10n_it_cee_balance.' \
                          'cee_balance_report_qweb'
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1).report_action(self)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'l10n_it_cee_balance.cee_balance_report').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    @api.multi
    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.only_posted_moves,
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.filter_account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.filter_partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.filter_journal_ids.ids)],
            'fy_start_date': self.fy_start_date,
            'hierarchy_on': 'relation',
            'use_cee_group': True,
        }

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute Trial Balance Report Data.
        model = self.env['report_trial_balance']
        if self.filter_account_ids:
            account_ids = self.filter_account_ids
        else:
            account_ids = self.env['account.account'].search(
                [('company_id', '=', self.company_id.id)])
        self.trial_balance_id = model.create(
            self._prepare_report_trial_balance()
        )
        # Prepare params
        # params = self._prepare_report_trial_balance()
        # self.trial_balance_id.write(params)
        # Execure report
        self.trial_balance_id.compute_data_for_report()

        # Set accounts in right section
        for report_account in self.trial_balance_id.account_ids:
            account = report_account.account_id
            user_type = False
            if account.user_type_id:
                user_type = account.user_type_id.name

            print(user_type)

            val = {
                'report_id' : self.id,
                'hide_line' : report_account.hide_line,
                'sequence' : report_account.sequence,
                'level' : report_account.level,
                'account_id' : report_account.account_id.id,
                'account_group_cee_id' : report_account.account_group_cee_id.id,
                'parent_cee_id' : report_account.parent_cee_id.id,
                'code' : report_account.code,
                'name' : report_account.name,
                'currency_id' : report_account.currency_id.id,
                'initial_balance' : report_account.initial_balance,
                'initial_balance_foreign_currency' : \
                    report_account.initial_balance_foreign_currency,
                'debit' : report_account.debit,
                'credit' : report_account.credit,
                'period_balance' : report_account.period_balance,
                'final_balance' : report_account.final_balance,
                'final_balance_foreign_currency' : \
                    report_account.final_balance_foreign_currency,
                }
            # if report_account.account_group_cee_id.id == 24:
            #     import pdb;pdb.set_trace()
            # print(val)

            self.env['report_cee_balance_report_account'].create(val)

            """
            if section_debit_ids:
                # self.section_debit_ids = [(6, 0, section_debit_ids)]
                self.section_debit_ids = section_debit_ids
            if section_credit_ids:
                self.section_credit_ids = [(6, 0, section_credit_ids)]"""


class TrialBalanceReport(models.TransientModel):
    _inherit = 'report_trial_balance'

    use_cee_group = fields.Boolean()


class TrialBalanceReportCompute(models.TransientModel):
    _inherit = 'report_trial_balance'

    def _inject_account_group_values(self):
        # if not self.use_cee_group:
        #     return super()._inject_account_group_values()
        """Inject report values for report_trial_balance_account"""
        query_inject_account_group = """
INSERT INTO
    report_trial_balance_account
    (
    report_id,
    create_uid,
    create_date,
    account_group_cee_id,
    parent_cee_id,
    code,
    name,
    sequence,
    level
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    accgroup.id,
    accgroup.parent_id,
    coalesce(accgroup.code_prefix, accgroup.name),
    accgroup.name,
    accgroup.parent_path,
    accgroup.level
FROM
    account_group_cee accgroup"""
        query_inject_account_params = (
            self.id,
            self.env.uid,
        )
        self.env.cr.execute(query_inject_account_group,
                            query_inject_account_params)

    def _update_account_group_computed_values(self):
        """Compute values for report_trial_balance_account group in compute."""
        query_update_account_group = """
WITH RECURSIVE accgroup AS
(SELECT
    accgroup.id,
    sum(coalesce(ra.initial_balance, 0)) as initial_balance,
    sum(coalesce(ra.initial_balance_foreign_currency, 0))
        as initial_balance_foreign_currency,
    sum(coalesce(ra.debit, 0)) as debit,
    sum(coalesce(ra.credit, 0)) as credit,
    sum(coalesce(ra.debit, 0)) - sum(coalesce(ra.credit, 0)) as period_balance,
    sum(coalesce(ra.final_balance, 0)) as final_balance,
    sum(coalesce(ra.final_balance_foreign_currency, 0))
        as final_balance_foreign_currency
 FROM
    account_group_cee accgroup
    LEFT OUTER JOIN account_account AS acc
        ON strpos(acc.code, accgroup.code_prefix) = 1
    LEFT OUTER JOIN report_trial_balance_account AS ra
        ON ra.account_id = acc.id
 WHERE ra.report_id = %s
 GROUP BY accgroup.id
)
UPDATE report_trial_balance_account
SET initial_balance = accgroup.initial_balance,
    initial_balance_foreign_currency =
        accgroup.initial_balance_foreign_currency,
    debit = accgroup.debit,
    credit = accgroup.credit,
    period_balance = accgroup.period_balance,
    final_balance = accgroup.final_balance,
    final_balance_foreign_currency =
        accgroup.final_balance_foreign_currency

FROM accgroup
WHERE report_trial_balance_account.account_group_cee_id = accgroup.id
"""
        query_update_account_params = (self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _update_account_sequence(self):
        """Compute sequence, level for report_trial_balance_account account."""
        query_update_account_group = """
UPDATE report_trial_balance_account
SET sequence = CONCAT(newline.sequence, newline.code),
    level = newline.level + 1
FROM report_trial_balance_account as newline
WHERE newline.account_group_cee_id = report_trial_balance_account.parent_cee_id
    AND report_trial_balance_account.report_id = newline.report_id
    AND report_trial_balance_account.account_id is not null
    AND report_trial_balance_account.report_id = %s"""
        query_update_account_params = (self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _add_account_group_account_values(self):
        """Compute values for report_trial_balance_account group in child."""
        query_update_account_group = """
DROP AGGREGATE IF EXISTS array_concat_agg(anyarray);
CREATE AGGREGATE array_concat_agg(anyarray) (
  SFUNC = array_cat,
  STYPE = anyarray
);
WITH aggr AS(WITH computed AS (WITH RECURSIVE cte AS (
   SELECT account_group_cee_id, account_group_cee_id AS parent_cee_id,
    ARRAY[account_id]::int[] as child_account_ids
   FROM   report_trial_balance_account
   WHERE report_id = %s
   GROUP BY report_trial_balance_account.id

   UNION  ALL
   SELECT c.account_group_cee_id, p.account_group_cee_id, ARRAY[p.account_id]::int[]
   FROM   cte c
   JOIN   report_trial_balance_account p USING (parent_cee_id)
    WHERE p.report_id = %s
)
SELECT account_group_cee_id,
    array_concat_agg(DISTINCT child_account_ids)::int[] as child_account_ids
FROM   cte
GROUP BY cte.account_group_cee_id, cte.child_account_ids
ORDER BY account_group_cee_id
)
SELECT account_group_cee_id,
    array_concat_agg(DISTINCT child_account_ids)::int[]
        AS child_account_ids from computed
GROUP BY account_group_cee_id)
UPDATE report_trial_balance_account
SET child_account_ids = aggr.child_account_ids
FROM aggr
WHERE report_trial_balance_account.account_group_cee_id = aggr.account_group_cee_id
    AND report_trial_balance_account.report_id = %s
"""
        query_update_account_params = (self.id, self.id, self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)

    def _update_account_group_child_values(self):
        """Compute values for report_trial_balance_account group in child."""
        query_update_account_group = """
WITH computed AS (WITH RECURSIVE cte AS (
   SELECT account_group_cee_id, code, account_group_cee_id AS parent_cee_id,
    initial_balance, initial_balance_foreign_currency, debit, credit,
    period_balance, final_balance, final_balance_foreign_currency
   FROM   report_trial_balance_account
   WHERE report_id = %s
   GROUP BY report_trial_balance_account.id

   UNION  ALL
   SELECT c.account_group_cee_id, c.code, p.account_group_cee_id,
    p.initial_balance, p.initial_balance_foreign_currency, p.debit, p.credit,
    p.period_balance, p.final_balance, p.final_balance_foreign_currency
   FROM   cte c
   JOIN   report_trial_balance_account p USING (parent_cee_id)
    WHERE p.report_id = %s
)
SELECT account_group_cee_id, code,
    sum(initial_balance) AS initial_balance,
    sum(initial_balance_foreign_currency) AS initial_balance_foreign_currency,
    sum(debit) AS debit,
    sum(credit) AS credit,
    sum(debit) - sum(credit) AS period_balance,
    sum(final_balance) AS final_balance,
    sum(final_balance_foreign_currency) AS final_balance_foreign_currency
FROM   cte
GROUP BY cte.account_group_cee_id, cte.code
ORDER BY account_group_cee_id
)
UPDATE report_trial_balance_account
SET initial_balance = computed.initial_balance,
    initial_balance_foreign_currency =
        computed.initial_balance_foreign_currency,
    debit = computed.debit,
    credit = computed.credit,
    period_balance = computed.period_balance,
    final_balance = computed.final_balance,
    final_balance_foreign_currency =
        computed.final_balance_foreign_currency
FROM computed
WHERE report_trial_balance_account.account_group_cee_id = computed.account_group_cee_id
    AND report_trial_balance_account.report_id = %s
"""
        query_update_account_params = (self.id, self.id, self.id,)
        self.env.cr.execute(query_update_account_group,
                            query_update_account_params)


    def _compute_group_accounts(self):
        groups = self.account_ids.filtered(
            lambda a: a.account_group_cee_id is not False)
        for group in groups:
            #>>>>>
            # if group.account_group_cee_id.id == 24:
            #     import pdb;pdb.set_trace()
            if group.account_group_cee_id \
                    and group.account_group_cee_id.account_ids:
                group.child_account_ids = \
                    group.account_group_cee_id.account_ids
                group.compute_account_ids = \
                    [(6, 0, group.account_group_cee_id.account_ids.ids)]
            #<<<<<
            """
            if self.hierarchy_on == 'computed':
                group.compute_account_ids = \
                    group.account_group_cee_id.compute_account_ids
            else:
                if group.child_account_ids:
                    chacc = group.child_account_ids.replace(
                        '}', '').replace('{', '').split(',')
                    if 'NULL' in chacc:
                        chacc.remove('NULL')
                    if chacc:
                        group.compute_account_ids = [
                            (6, 0, [int(g) for g in chacc])]
                            """


class TrialBalanceReportAccount(models.TransientModel):
    _inherit = 'report_trial_balance_account'

    account_group_cee_id = fields.Many2one(
        'account.group.cee',
        index=True
    )
    parent_cee_id = fields.Many2one(
        'account.group.cee',
        index=True
    )
