odoo.define('pos_example', function (require) {
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var QWeb = core.qweb;
    var session = require('web.session');
    // var QWeb = require('web.qweb');
    // var session = require('session');

    // var rpc = require('web.rpc');

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            if (this.pos.config.pos_auto_invoice) {
                this.to_invoice = true;
            }
             if (this.pos.config.pos_auto_customer_guest) {
                 this.set('selectedClient', this.pos.config.pos_auto_customer_guest_id );
                 if (this.pos.config.pos_auto_customer_guest_id) {
                    client = this.pos.db.get_partner_by_id(this.pos.config.pos_auto_customer_guest_id);
                 if (!client) {
                    console.error('ERROR: trying to load a parner not available in the pos');
                }
                } else {
                    client = null;
                }
                this.set_client(client);
                }
        },
         init_from_JSON: function (json) {
             var res = _super_Order.init_from_JSON.apply(this, arguments);
             if (json.to_invoice) {
                 this.to_invoice = json.to_invoice;
             }
         }
    });
    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
             var partner_model = _.find(this.models, function (model) {
                return model.model === 'res.partner';
            });
            partner_model.fields.push('vat');
            _super_PosModel.initialize.apply(this, arguments);
        },
        push_and_invoice_order: function () {
            var self = this;
            return _super_PosModel.push_and_invoice_order.apply(this, arguments).then(function () {
                var order = self.get_order();
                self.order = order;
                if (order.is_to_invoice()) {

                    return new Model('pos.order')
                .query(['invoice_id'])
                .filter([['pos_reference', '=', order['name']]])
                .all().then(function (orders) {
                        if (orders.length >= 1) {
                            var invoice = orders[0]['invoice_id']
                            return new Model('account.invoice')
                            .query(['zoi','eor','fiskalni_broj','qrcode'])
                            .filter([['id', '=', invoice[0]]])
                            .all().then(function (invoices) {
                                if (invoices.length >= 1) {
                                    self.order.invoice_number = invoices[0]['zoi']
                                    self.order.invoice = invoices[0]



                                }
                            }).fail(function (error) {
                            })
                        }
                    }).fail(function (error) {
                    })
                }
            });
        }
    })
});
