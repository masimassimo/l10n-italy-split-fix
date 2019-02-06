odoo.define('l10n_it_website_portal_fatturapa', function(require) {
    'use strict';

    var ajax = require('web.ajax');
    var base = require('web_editor.base');


    var details_div_selector = '.o_website_portal_details';
    var $details_div = $(details_div_selector);
    if(!$details_div.length) {
        return $.Deferred().reject("DOM doesn't contain " + details_div_selector);
    }

    // is_pa, ipa_code management
    var $is_pa_input = $details_div.find("input[name='is_pa'][type='checkbox']");
    var $ipa_code_input = $details_div.find("input[name='ipa_code']");
    var $ipa_code_div = $details_div.find(".div_ipa_code");

    var compute_ipa_code_visibility = function(){
        if ($is_pa_input[0].checked) {
            $ipa_code_div.removeClass("hidden");
        } else {
            $ipa_code_div.addClass("hidden");
        }
    };
    compute_ipa_code_visibility();
    
    $is_pa_input.change(compute_ipa_code_visibility);
});
