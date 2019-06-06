from odoo import models, fields, api
from odoo.osv import expression


class AccountGroupCEE(models.Model):
    _name = "account.group.cee"
    _description = 'Account Group CEE'
    _parent_store = True
    _order = 'code_prefix'

    parent_id = fields.Many2one(
        'account.group.cee', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    name = fields.Char(required=True)
    code_prefix = fields.Char()
    # See account-financial-reporting:
    group_child_ids = fields.One2many(
        comodel_name='account.group.cee',
        inverse_name='parent_id',
        string='Child Groups')
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True)
    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='cee_group_id',
        string="Accounts")
    compute_account_ids = fields.Many2many(
        'account.account',
        compute='_compute_group_accounts',
        string="Compute accounts", store=True)

    @api.multi
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for group in self:
            if not group.parent_id:
                group.level = 0
            else:
                group.level = group.parent_id.level + 1

    @api.multi
    @api.depends('code_prefix', 'account_ids', 'account_ids.code',
                 'group_child_ids', 'group_child_ids.account_ids.code')
    def _compute_group_accounts(self):
        account_obj = self.env['account.account']
        accounts = account_obj.search([])
        for group in self:
            prefix = group.code_prefix if group.code_prefix else group.name
            gr_acc = accounts.filtered(
                lambda a: a.code.startswith(prefix)).ids
            group.compute_account_ids = [(6, 0, gr_acc)]

    def name_get(self):
        result = []
        for group in self:
            name = group.name
            if group.code_prefix:
                name = group.code_prefix + ' ' + name
            result.append((group.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
            domain = criteria_operator + [('code_prefix', '=ilike', name + '%'), ('name', operator, name)]
        group_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(group_ids).name_get()


class Account(models.Model):
    _inherit = 'account.account'
    cee_group_id = fields.Many2one('account.group.cee', string="CEE group")
