odoo.define("fiscal_epos_print.screens", function (require) {
    "use strict";

    var core = require("web.core");
    var screens = require('point_of_sale.screens');
    var epson_epos_print = require('fiscal_epos_print.epson_epos_print');
    var _t = core._t;
    var PaymentScreenWidget = screens.PaymentScreenWidget;
    var ReceiptScreenWidget = screens.ReceiptScreenWidget;
    var eposDriver = epson_epos_print.eposDriver;

    ReceiptScreenWidget.include({
        show: function(){
            if (!this.pos.config.printer_ip || (this.pos.config.printer_ip && this.pos.config.show_receipt_when_printing) ){
                this._super();
            }
            else
            {
                this.click_next();
            }
        }
    });

    PaymentScreenWidget.include({
        getPrinterOptions: function (){
            var protocol = ((this.pos.config.use_https) ? 'https://' : 'http://');
            var printer_url = protocol + this.pos.config.printer_ip + '/cgi-bin/fpmate.cgi';
            return {url: printer_url};
        },
        sendToFP90Printer: function(receipt, printer_options) {
            var fp90 = new eposDriver(printer_options, this);
            fp90.printFiscalReceipt(receipt);
        },
        finalize_validation: function() {
            // we need to get currentOrder before calling the _super()
            // otherwise we will likely get a empty order when we want to skip
            // the receipt preview
            var currentOrder = this.pos.get('selectedOrder');
            this._super.apply(this, arguments);
            if (this.pos.config.printer_ip && !currentOrder.is_to_invoice()) {
                var printer_options = this.getPrinterOptions();
                var receipt = currentOrder.export_for_printing();
                this.sendToFP90Printer(receipt, printer_options);
                currentOrder._printed = true;
            }
        },
        order_is_valid: function(force_validation) {
            var self = this;
            var receipt = this.pos.get_order();
            if (receipt.has_refund && (receipt.refund_date == null || receipt.refund_date === '' ||
                                       receipt.refund_doc_num == null || receipt.refund_doc_num == '' ||
                                       receipt.refund_cash_fiscal_serial == null || receipt.refund_cash_fiscal_serial == '' ||
                                       receipt.refund_report == null || receipt.refund_report == '')) {
                    this.gui.show_popup('error',{
                        'title': _t('Refund Information Not Present'),
                        'body':  _t("The refund information aren't present. Please insert them before printing the receipt"),
                    });
                    return false;
            }
            return this._super(force_validation);
        }
    });

    var set_refund_info_button = screens.ActionButtonWidget.extend({
        template: 'SetRefundInfoButton',
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.pos.bind('change:selectedOrder',function(){
                this.orderline_change();
                this.bind_order_events();
            },this);
            this.bind_order_events();
            this.orderline_change();
        },
        renderElement: function() {
            this._super();
            var color = this.refund_get_button_color();
            this.$el.css('background', color);
        },
        button_click: function () {
            var self = this;
            var current_order = self.pos.get_order();
            self.gui.show_popup('refundinfo', {
                title: _t('Refund Information Details'),
                refund_date: current_order.refund_date,
                refund_report: current_order.refund_report,
                refund_doc_num: current_order.refund_doc_num,
                refund_cash_fiscal_serial: current_order.refund_cash_fiscal_serial,
                update_refund_info_button: function(){
                    self.renderElement();
                },
            });
        },
        bind_order_events: function() {
            var self = this;
            var order = this.pos.get_order();

            if (!order) {
                return;
            }

            if(this.old_order) {
                this.old_order.unbind(null,null,this);
            }

            this.pos.bind('change:selectedOrder', this.orderline_change, this);

            var lines = order.orderlines;
                lines.unbind('add',     this.orderline_change, this);
                lines.bind('add',       this.orderline_change, this);
                lines.unbind('remove',  this.orderline_change, this);
                lines.bind('remove',    this.orderline_change, this);
                lines.unbind('change',  this.orderline_change, this);
                lines.bind('change',    this.orderline_change, this);

            this.old_order = order;
        },
        refund_get_button_color: function() {
            var order = this.pos.get_order();
            var lines = order.orderlines;
            var has_refund = lines.find(function(line){ return line.quantity < 0.0;}) != undefined;
            var color = '#e2e2e2';
            if (has_refund == true)
            {
                if (order.refund_date && order.refund_date != '' && order.refund_doc_num && order.refund_doc_num != '' &&
                    order.refund_cash_fiscal_serial && order.refund_cash_fiscal_serial != '' && order.refund_report && order.refund_report != '') {
                        color = 'lightgreen';
                }
                else
                {
                    color = 'red';
                }
            }
            return color;
        },
        orderline_change: function(){
            var order = this.pos.get_order();
            var lines = order.orderlines;
            order.has_refund = lines.find(function(line){ return line.quantity < 0.0;}) != undefined;
            this.renderElement();
        },
    });

    screens.define_action_button({
        'name': 'set_refund_info',
        'widget': set_refund_info_button,
    });

    return {
        RefundInfoButtonActionWidget: set_refund_info_button
    };

});
