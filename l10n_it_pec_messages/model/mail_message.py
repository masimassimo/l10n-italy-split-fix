# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Associazione Odoo Italia
#    (<http://www.odoo-italia.org>).
#    Copyright 2014 Agile Business Group http://www.agilebg.com
#    @authors
#       Alessio Gerace <alessio.gerace@gmail.com>
#       Lorenzo Battistini <lorenzo.battistini@agilebg.com>
#       Roberto Onnis <roberto.onnis@innoviu.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _


class MailMessage(orm.Model):
    _inherit = "mail.message"

    def _get_is_pec(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        mail_pool = self.pool['mail.mail']
        for message in self.browse(cr, uid, ids, context=context):
            res[message.id] = False
            mail_ids = mail_pool.search(
                cr, uid, [('mail_message_id', '=', message.id)],
                context=context)
            if len(mail_ids) > 1:
                raise orm.except_orm(
                    _('Error'),
                    _('Too many mails for message %s') % message.id)
            if mail_ids:
                mail = mail_pool.browse(cr, uid, mail_ids[0], context=context)
                if mail.fetchmail_server_id and mail.fetchmail_server_id.pec:
                    res[message.id] = True
        return res

    def _get_message_by_mail(self, cr, uid, ids, context=None):
        res = {}
        for mail in self.pool['mail.mail'].browse(
            cr, uid, ids, context=context
        ):
            res[mail.mail_message_id] = True
        return res.keys()

    def _get_message_by_server(self, cr, uid, ids, context=None):
        res = {}
        mail_pool = self.pool['mail.mail']
        mail_ids = mail_pool.search(
            cr, uid, [('fetchmail_server_id', 'in', ids)], context=context)
        for mail in mail_pool.browse(cr, uid, mail_ids, context=context):
            if mail.mail_message_id:
                res[mail.mail_message_id.id] = True
        return res.keys()

    _columns = {
        # this doesn not seem to work because mail.mail is not created by
        # fetchmail
        'pec': fields.function(
            _get_is_pec, type="boolean", string="PEC mail",
            store={
                'mail.mail': (
                    _get_message_by_mail,
                    ['mail_message_id', 'fetchmail_server_id'], 10),
                'fetchmail.server': (_get_message_by_server, ['pec'], 10),
                }),
        'pec_type': fields.selection([
            ('posta-certificata', 'Pec Mail'),
            ('accettazione', 'Reception'),
            ('presa-in-carico', 'In Progress'),
            ('avvenuta-consegna', 'Delivery'),
            ('errore-consegna', 'Delivery Error'),
            ('preavviso-errore-consegna', 'Notice Delivery Error'),
            ('rilevazione-virus', 'Virus Detected'),
            ], 'Pec Type', readonly=True),
        'cert_datetime': fields.datetime(
            'Certified Date and Time ', readonly=True),
        'pec_msg_id': fields.char(
            'PEC-Message-Id',
            help='Message unique identifier', select=1, readonly=True),
        'ref_msg_id': fields.char(
            'ref-Message-Id',
            help='Ref Message unique identifier', select=1, readonly=True),
        'delivery_message_id': fields.many2one(
            'mail.message', 'Delivery Message', readonly=True),
        'reception_message_id': fields.many2one(
            'mail.message', 'Reception Message', readonly=True),
    }

    def get_datafrom_daticertxml(self,daticertxml,contex=None):
        ret={}
        content = self.getFile(daticertxml).decode('base64')
        daticert = ElementTree(fromstring(content))

    def _search(
        self, cr, uid, args, offset=0, limit=None, order=None,
        context=None, count=False, access_rights_uid=None
    ):
        if context is None:
            context = {}
        if context.get('pec_messages'):
            return super(orm.Model, self)._search(
                cr, uid, args, offset=offset, limit=limit, order=order,
                context=context, count=count,
                access_rights_uid=access_rights_uid)
        else:
            return super(MailMessage, self)._search(
                cr, uid, args, offset=offset, limit=limit, order=order,
                context=context, count=count,
                access_rights_uid=access_rights_uid)

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        if context is None:
            context = {}
        if context.get('pec_messages'):
            return super(orm.Model, self).check_access_rule(
                cr, uid, ids, operation, context=context)
        else:
            return super(MailMessage, self).check_access_rule(
                cr, uid, ids, operation, context=context)
