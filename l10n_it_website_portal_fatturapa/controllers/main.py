# -*- coding: utf-8 -*-
# Copyright 2019 Simone Rubino
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.l10n_it_website_portal_fiscalcode.controllers.main import \
    WebsitePortalFiscalCode

FATTURAPA_PORTAL_FIELDS = \
    ['is_pa', 'ipa_code', 'codice_destinatario', 'firstname', 'lastname',
     'pec_mail', 'country_id', 'fiscalcode', 'zipcode', 'vat']
WebsitePortalFiscalCode.OPTIONAL_BILLING_FIELDS.extend(FATTURAPA_PORTAL_FIELDS)


class WebsitePortalFatturapa(WebsitePortalFiscalCode):

    def details_form_validate(self, data):
        error, error_message = \
            super(WebsitePortalFatturapa, self).details_form_validate(data)
        partner_model = request.env['res.partner']
        partner_sudo = request.env.user.partner_id.sudo()
        # Compute name field, using First name and Last name
        if all(f in data for f in ['name', 'firstname', 'lastname']):
            partner_model = request.env['res.partner']
            data.update(
                name=partner_model._get_computed_name(
                    data['lastname'],
                    data['firstname']))

        # Read all the fields for the constraint from the current user
        constr_fields = partner_sudo._check_ftpa_partner_data._constrains
        partner_values = partner_sudo.read(constr_fields)[0]

        # Update them with fields that might be edited by the user
        new_partner_values = {f_name: data.get(f_name)
                              for f_name in FATTURAPA_PORTAL_FIELDS}
        if 'country_id' in new_partner_values:
            new_partner_values['country_id'] = \
                int(new_partner_values['country_id'])
        new_partner_values.update({
            'zip': new_partner_values.pop('zipcode', '')})

        partner_values.update(new_partner_values)
        dummy_partner = partner_model.new(partner_values)
        try:
            dummy_partner._check_ftpa_partner_data()
        except ValidationError as ve:
            error['error'] = 'Error'
            error_message.append(ve.name)
        return error, error_message
