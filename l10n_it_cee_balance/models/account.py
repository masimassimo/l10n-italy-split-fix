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
