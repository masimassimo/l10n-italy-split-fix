from odoo import models


class WizardExportFatturapa(models.TransientModel):
    _inherit = "wizard.export.fatturapa"

    def saveAttachment(self, fatturapa, number, existing_attachment=None):
        res = super(WizardExportFatturapa, self).saveAttachment(
            fatturapa, number, existing_attachment)
        if existing_attachment:
            res.state = 'ready'
        return res
