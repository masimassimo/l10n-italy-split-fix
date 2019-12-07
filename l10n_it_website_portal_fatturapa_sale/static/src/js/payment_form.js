odoo.define('l10n_it_website_portal_fatturapa_sale.payment_form', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var PaymentForm = require('payment.payment_form');

    PaymentForm.include({
        payEvent: function (ev) {
            var partner_id = this.options.partnerId;
            var super_pay_event = this._super;
            var self = this;
            var self_args = arguments;
            if (partner_id) {
                var form = this.el;
                var inv_subj =
                    form.elements.electronic_invoice_subjected.checked;

                return ajax.jsonRpc('/my/orders/check-e-invoice-partner-data', 'call', {
                        'partner_id': partner_id,
                        'inv_subj': inv_subj
                    }).then(
                    function (result){
                        if (result)
                            return super_pay_event.apply(self, self_args);
                        // Write did not succeed: redirect to details
                        var redirect_url = "/my/account";
                        var params = {
                            redirect: window.location.pathname,
                        };
                        if (inv_subj)
                            params.electronic_invoice_subjected = 'on';
                        window.location = redirect_url + "?" + $.param(params);
                    }
                );
            }
        },
    });
});
