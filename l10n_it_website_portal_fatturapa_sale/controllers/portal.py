from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class CustomerPortal(CustomerPortal):

    @http.route(
        ['/my/orders/check-e-invoice-partner-data'], type='json', auth="public",
        website=True
    )
    def sale_portal_check_e_invoice_data(self, partner_id, inv_subj):
        if inv_subj:
            # If not selected, e-inv data is not needed and we don't want to write
            # False to electronic_invoice_subjected
            try:
                partner = request.env['res.partner'].browse(partner_id)
                partner.sudo().electronic_invoice_subjected = inv_subj
            except ValidationError:
                return False
        return True
