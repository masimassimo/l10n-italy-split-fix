# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models, exceptions


class CommunicationInvoicesDataRicalcoloTipoDocumentoFiscale(models.TransientModel):
    _name = "communication.invoices.data.ricalcolo.tipo.document.fiscale"
    _description = "Ricalcolo tipo documento fiscale su fatture"

    @api.multi
    def compute(self):
        communication_ids = self._context.get('active_ids')
        for wizard in self:
            for comunicazione in self.env['communication.invoices.data'].\
                    browse(communication_ids):
                domain = [('communication_invoices_data_escludi', '=', True)]
                no_journal_ids = self.env['account.journal'].search(domain).ids
                domain = [
                    ('move_id', '!=', False),
                    ('communication_invoices_data_escludi', '!=', True),
                    ('move_id.journal_id', 'not in', no_journal_ids),
                    ('company_id', '>=', comunicazione.company_id.id),
                    ('date_invoice', '>=', comunicazione.date_start),
                    ('date_invoice', '<=', comunicazione.date_end)]
                fatture = self.env['account.invoice'].search(domain)
                for fattura in fatture:
                    fattura.fiscal_document_type_id =\
                        fattura._get_document_fiscal_type(
                            type=fattura.type, partner=fattura.partner_id,
                            fiscal_position=fattura.fiscal_position_id,
                            journal=fattura.journal_id)[0] or False
            return {}
