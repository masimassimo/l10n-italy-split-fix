# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models, exceptions


class CommunicationInvoicesDataExportFile(models.TransientModel):
    _name = "communication.invoices.data.export.file"
    _description = "Export file xml della comunicazione dei dati IVA"

    file_export = fields.Binary('File', readonly=True)
    filename = fields.Char()
    name = fields.Char('File Name', readonly=True, default='dati_iva.xml')

    @api.multi
    def export(self):

        communication_ids = self._context.get('active_ids')
        if not communication_ids:
            raise exceptions.Warning(
                u'Attenzione! Nessuna comunicazione selezionata'
            )
        if len(communication_ids) > 1:
            raise exceptions.Warning(
                u'Attenzione! '
                u'È possibile esportare una sola comunicazione alla volta'
            )

        for wizard in self:
            for comunicazione in self.env['communication.invoices.data'].\
                    browse(communication_ids):
                out = base64.encodestring(comunicazione.get_export_xml())
                filename = comunicazione.get_export_xml_filename()
                wizard.file_export = out
                wizard.filename = filename
            model_data_obj = self.env['ir.model.data']
            view_rec = model_data_obj.get_object_reference(
                'l10n_it_invoices_data_communication',
                'wizard_dati_iva_export_file_exit'
            )
            view_id = view_rec and view_rec[1] or False

            return {
                'view_type': 'form',
                'view_id': [view_id],
                'view_mode': 'form',
                'res_model': 'communication.invoices.data.export.file',
                'res_id': wizard.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
}