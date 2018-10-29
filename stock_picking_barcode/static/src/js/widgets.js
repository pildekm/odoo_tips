odoo.define('stock_picking_barcode.widgets', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var Model = require('web.Model');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var data = require('web.data');
    var web_client = require('web.web_client');
    var session = require('web.session');
    var _t = core._t;
    var qweb = core.qweb;

    // This widget makes sure that the scaling is disabled on mobile devices.
    // Widgets that want to display fullscreen on mobile phone need to extend this
    // widget.

    var MobileWidget = Widget.extend({
        start: function(){
            if(!$('#oe-mobilewidget-viewport').length){
                $('head').append('<meta id="oe-mobilewidget-viewport" name="viewport" content="initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">');
            }
            return this._super();
        },
        destroy: function(){
            $('#oe-mobilewidget-viewport').remove();
            return this._super();
        }
    });



    var PickingEditorWidget = Widget.extend({
        template: 'PickingEditorWidget',
        init: function(parent){
            this._super(parent);
            var self = this;
            this.rows = [];
            this.picking_cases = {};
            this.picking_cases = parent.picking_cases
            this.search_filter = "";
            jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
                return function( elem ) {
                    return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
                };
            });
        },
        get_header: function(){
            return this.getParent().get_header();
        },
        get_location: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;
            _.each(model.locations, function(loc){
                locations.push({name: loc.complete_name, id: loc.id});
            });
            return locations;
        },
        get_picking_cases: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;



            return self.picking_cases;
        },
        goto_pickings_by_case: function(picking_order_id,case_number){
            var self = this;
            //$.bbq.pushState('#action=stock_invoice.pick&picking_order_id='+picking_order_id+'&case_number='+case_number);
            // $(window).trigger('hashchange');
             var model = this.getParent();

             this.$('.oe_pick_app_header').text(model.get_header());
             model.refresh_ui(parseInt(picking_order_id),parseInt(case_number));

        },

        get_logisticunit: function(){
            var model = this.getParent();
            var ul = [];
            var self = this;
            _.each(model.uls, function(ulog){
                ul.push({name: ulog.name, id: ulog.id});
            });
            return ul;
        },
        validate: function(picking_order_id){
            var self = this;

            return new Model('picking.invoice.validation').call('transfer_from_ui',[0,picking_order_id]).then(function(new_picking_ids){
                // if (new_picking_ids) {
                //     // TODO DODAJ CASE
                //     return self.refresh_ui(new_picking_ids[0]);
                // }
                console.log(picking_order_id);

                return 0;
            });


        },

        get_rows: function(){
            var self = this;
            var model = this.getParent();
            this.rows = [];
            var self = this;
            var pack_created = [];



            _.each( model.packoplines, function(packopline){


                var color = "";'';
                if (typeof packopline.product_id[1] !== 'undefined') {
                    var pack = packopline.package_id[1];
                }
                // TODO DODAJ PREVERJANJE za picking_invoice_line.qty_done

                if (packopline.product_qty === packopline.qty_done){
                    color = "success ";
                }
                if (packopline.product_qty < packopline.qty_done){
                    color = "danger ";
                }
                //also check that we don't have a line already existing for that package
                if (typeof packopline.result_package_id[1] !== 'undefined' && $.inArray(packopline.result_package_id[0], pack_created) === -1){
                    var myPackage = $.grep(model.packages, function(e){
                        return e.id === packopline.result_package_id[0];
                    })[0];
                    self.rows.push({
                        cols: { product: packopline.result_package_id[1],
                            qty: '',
                            rem: '',
                            uom: void 0,
                            lots: void 0,
                            pack: void 0,
                            container: packopline.result_package_id[1],
                            container_id: void 0,
                            loc: packopline.location_id[1],
                            dest: packopline.location_dest_id[1],
                            id: packopline.result_package_id[0],
                            product_id: void 0,
                            can_scan: false,
                            head_container: true,
                            processed_boolean: packopline.processed_boolean,
                            package_id: myPackage.id,
                            ul_id: myPackage.ul_id[0],
                            dest_info_text: packopline.dest_info_text
                        },
                        classes: ('success container_head ') + (packopline.processed_boolean === "true"
                            ? 'processed hidden '
                            :'')
                    });
                    pack_created.push(packopline.result_package_id[0]);
                }
                var lots = _.map(packopline.pack_lot_ids || [], function(id){
                    var op_lot = model.op_lots_index[id];
                    return op_lot.lot_name || op_lot.lot_id[1];
                });
                lots = lots.join(',');


                self.rows.push({
                    cols: { product: packopline.product_id[1] || packopline.package_id[1],
                        //TODO Gregor qty: packopline.product_qty,
                        qty: packopline.product_qty,
                        rem: packopline.qty_done,
                        uom: packopline.product_uom_id[1],
                        lots: lots,
                        pack: pack,
                        container: packopline.result_package_id,
                        container_id: packopline.result_package_id[0],
                        loc: packopline.location_id[1],
                        dest: packopline.location_dest_id[1],
                        id: packopline.id,
                        product_id: packopline.product_id[0],
                        can_scan: (typeof packopline.result_package_id[1] === 'undefined'),
                        head_container: false,
                        processed_boolean: packopline.processed_boolean,
                        package_id: void 0,
                        ul_id: -1,
                        dest_info_text: packopline.dest_info_text
                    },

                    classes: color + (typeof packopline.result_package_id[1] === 'undefined'
                        ? ''
                        : 'in_container_hidden ') + (packopline.processed_boolean === "true"
                        ? 'processed hidden '
                        :''
                        )
                });

            });
            //sort element by things to do, then things done, then grouped by packages
            var group_by_container = _.groupBy(self.rows, function(row){
                return row.cols.container;
            });
            var sorted_row = [];
            if (typeof group_by_container.undefined !== 'undefined'){
                group_by_container.undefined.sort(function(a,b) {
                    return (b.classes === '') - (a.classes === '');
                });
                $.each(group_by_container.undefined, function(key, value){
                    sorted_row.push(value);
                });
            }

            $.each(group_by_container, function(key, value){
                if (key !== 'undefined'){
                    $.each(value, function(k,v){
                        sorted_row.push(v);
                    });
                }
            });

            return sorted_row;
        },
        renderElement: function(){
            // TODO Tle je bug
            var self = this;

            this._super();
            this.check_content_screen();
            this.$('.js_pick_done').click(function(){
                self.getParent().done();
            });
            this.$('.js_pick_print').click(function(){
                self.getParent().print_picking();
            });
            this.$('.oe_pick_app_header').text(self.get_header());
            this.$('.oe_searchbox').keyup(function(event){
                self.on_searchbox($(this).val());
            });
            this.$('.js_putinpack').click(function(){
                self.getParent().pack();
            });
            //TODO f ja za case done
            this.$('.js_case_done').click(function(){
                self.getParent().case_done();
            });
            this.$('.js_validate_invoice').click(function(){
                var picking_order_id = self.getParent().picking_order_id;
                self.validate(picking_order_id);

            });

            this.$('.js_pick_all').click(function(){
                self.getParent().pick_all();
            });
            this.$('.js_drop_down').click(function(){
                self.getParent().drop_down();
            });
            this.$('.js_clear_search').click(function(){
                self.on_searchbox('');
                self.$('.oe_searchbox').val('');
            });
            this.$('.oe_searchbox').focus(function(){
                self.getParent().barcode_off();
            });
            this.$('.oe_searchbox').blur(function(){
                self.getParent().barcode_on();
            });
            this.$('.js_pick_search').click(function(){

                var ean = self.$('.search_cat_number').val();
                var quantity = self.$('.search_cat_quantity').val();

                self.getParent().scan(ean,quantity);
            });
            this.$('#js_select').change(function(){
                var selection = self.$('#js_select option:selected').attr('value');
                if (selection === "ToDo"){
                    self.getParent().$('.js_pick_pack').removeClass('hidden');
                    self.getParent().$('.js_drop_down').removeClass('hidden');
                    self.$('.js_pack_op_line.processed').addClass('hidden');
                    self.$('.js_pack_op_line:not(.processed)').removeClass('hidden');
                }else{
                    self.getParent().$('.js_pick_pack').addClass('hidden');
                    self.getParent().$('.js_drop_down').addClass('hidden');
                    self.$('.js_pack_op_line.processed').removeClass('hidden');
                    self.$('.js_pack_op_line:not(.processed)').addClass('hidden');
                }
                self.on_searchbox(self.search_filter);
            });
            this.$('.js_plus').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,true,'None');
            });
            this.$('.js_minus').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,false,'None');
            });
             this.$('.js_go_to_invoice_case').click(function(){
                var case_id = $(this).parents("[data-case-id]:first").data().caseId;
                var picking_order_id = self.getParent().picking_order_id;
                var model = self.getParent();
                model.case_number = case_id.toString()
                self.goto_pickings_by_case(parseInt(picking_order_id),case_id);

            });


            this.$('.js_unfold').click(function(){
                var op_id = $(this).parent().data('id');
                var line = $(this).parent();
                //select all js_pack_op_line with class in_container_hidden and correct container-id
                var select = self.$('.js_pack_op_line.in_container_hidden[data-container-id=' + op_id + ']');
                if (select.length > 0){
                    //we unfold
                    line.addClass('warning');
                    select.removeClass('in_container_hidden');
                    select.addClass('in_container');
                }else{
                    //we fold
                    line.removeClass('warning');
                    select = self.$('.js_pack_op_line.in_container[data-container-id='+op_id+']');
                    select.removeClass('in_container');
                    select.addClass('in_container_hidden');
                }
            });
            this.$('.js_create_lot').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var lot_name = false;
                self.$('.js_lot_scan').val('');
                var $lot_modal = self.$el.siblings('#js_LotChooseModal');
                //disconnect scanner to prevent scanning a product in the back while dialog is open
                self.getParent().barcode_off();
                $lot_modal.modal();
                //focus input
                $lot_modal.on('shown.bs.modal', function(){
                    self.$('.js_lot_scan').focus();
                });
                //reactivate scanner when dialog close
                $lot_modal.on('hidden.bs.modal', function(){
                    self.getParent().barcode_on();
                });
                self.$('.js_lot_scan').focus();
                //button action
                self.$('.js_validate_lot').click(function(){
                    //get content of input
                    var name = self.$('.js_lot_scan').val();
                    if (name.length !== 0){
                        lot_name = name;
                    }
                    $lot_modal.modal('hide');
                    //we need this here since it is not sure the hide event
                    //will be catch because we refresh the view after the create_lot call

                    self.getParent().barcode_on();
                    self.getParent().create_lot(op_id, lot_name);
                });
            });
            this.$('.js_delete_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().delete_package_op(pack_id);
            });
            this.$('.js_print_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                // $(this).parents("[data-id]:first").data('id')
                self.getParent().print_package(pack_id);
            });
            this.$('.js_submit_value').submit(function(event){
                var id = $(this).parents("[data-id]:first").data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($("input", this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(id, value);
                }
                $("input", this).val("");
                return false;
            });
            this.$('.js_qty').focus(function(){
                self.getParent().barcode_off();
            });
            this.$('.js_qty').blur(function(){
                var id = $(this).parent().parent().children("[data-product-id]:first").data('productId');
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($(this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(id, value);
                }
                self.getParent().barcode_on();
            });
            this.$('.js_change_src').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').addClass('source');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_pack_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').addClass('pack');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_validate_location').click(function(){
                //get current selection
                var select_dom_element = self.$('#js_loc_select');
                var loc_id = self.$('#js_loc_select option:selected').data('loc-id');
                var src_dst = false;
                var op_id = select_dom_element.data('op-id');
                if (select_dom_element.hasClass('pack')){
                    select_dom_element.removeClass('source');
                    var op_ids = [];
                    self.$('.js_pack_op_line[data-container-id='+op_id+']').each(function(){
                        op_ids.push($(this).data('id'));
                    });
                    op_id = op_ids;
                }else if (select_dom_element.hasClass('source')){
                    src_dst = true;
                    select_dom_element.removeClass('source');
                }
                if (loc_id === false){
                    //close window
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                }else{
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                    self.getParent().change_location(op_id, parseInt(loc_id), src_dst);

                }
            });
            this.$('.js_pack_configure').click(function(){
                var pack_id = $(this).parents(".js_pack_op_line:first").data('package-id');
                var ul_id = $(this).parents(".js_pack_op_line:first").data('ulid');
                self.$('#js_packconf_select').val(ul_id);
                self.$('#js_packconf_select').data('pack-id',pack_id);
                self.$el.siblings('#js_PackConfModal').modal();
            });
            this.$('.add_order_quantity').click(function(){
                //get current selection
                var select_dom_element = self.$('#js_packconf_select');
                var ul_id = self.$('#js_packconf_select option:selected').data('ul-id');
                var pack_id = select_dom_element.data('pack-id');
                self.$el.siblings('#js_PackConfModal').modal('hide');
                if (pack_id){
                    self.getParent().set_package_pack(pack_id, ul_id);
                    $('.container_head[data-package-id="'+pack_id+'"]').data('ulid', ul_id);
                }
            });

            //remove navigation bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        on_searchbox: function(query){
            //hide line that has no location matching the query and highlight location that match the query
            this.search_filter = query;
            var processed = ".processed";
            if (this.$('#js_select option:selected').attr('value') === "ToDo"){
                processed = ":not(.processed)";
            }
            if (query !== '') {
                this.$('.js_loc:not(.js_loc:Contains('+query+'))').removeClass('info');
                this.$('.js_loc:Contains('+query+')').addClass('info');
                this.$('.js_pack_op_line'+processed+':not(.js_pack_op_line:has(.js_loc:Contains('+query+')))').addClass('hidden');
                this.$('.js_pack_op_line'+processed+':has(.js_loc:Contains('+query+'))').removeClass('hidden');
            }
            //if no query specified, then show everything
            if (query === '') {
                this.$('.js_loc').removeClass('info');
                this.$('.js_pack_op_line'+processed+'.hidden').removeClass('hidden');
            }
            this.check_content_screen();
        },
        check_content_screen: function(){
            //get all visible element and if none has positive qty, disable put in pack and process button
            var self = this;
            var processed = this.$('.js_pack_op_line.processed');
            var qties = this.$('.js_pack_op_line:not(.processed):not(.hidden) .js_qty').map(function(){
                return $(this).val();
            });
            var container = this.$('.js_pack_op_line.container_head:not(.processed):not(.hidden)');
            var disabled = true;
            $.each(qties,function(index, value){
                if (parseInt(value)>0){
                    disabled = false;
                }
            });

            if (disabled){
                if (container.length===0){
                    self.$('.js_drop_down').addClass('disabled');
                }else{
                    self.$('.js_drop_down').removeClass('disabled');
                }
                self.$('.js_pick_pack').addClass('disabled');
                if (processed.length === 0){
                    self.$('.js_pick_done').addClass('disabled');
                }else{
                    self.$('.js_pick_done').removeClass('disabled');
                }
            }else{
                self.$('.js_drop_down').removeClass('disabled');
                self.$('.js_pick_pack').removeClass('disabled');
                self.$('.js_pick_done').removeClass('disabled');
            }
        },
        get_current_op_selection: function(ignore_container){
            //get ids of visible on the screen
            var pack_op_ids = [];
            this.$('.js_pack_op_line:not(.processed):not(.js_pack_op_line.hidden):not(.container_head)').each(function(){
                var cur_id = $(this).data('id');
                pack_op_ids.push(parseInt(cur_id));
            });
            //get list of element in this.rows where rem > 0 and container is empty is specified
            var list = [];
            _.each(this.rows, function(row){
                if (row.cols.rem > 0 && (ignore_container || typeof row.cols.container === 'undefined' || !row.cols.container)){
                    list.push(row.cols.id);
                }
            });
            //return only those visible with rem qty > 0 and container empty
            return _.intersection(pack_op_ids, list);
        },
        remove_blink: function(){
            this.$('.js_pack_op_line.blink_me').removeClass('blink_me');
        },
        blink: function(op_id){
            this.$('.js_pack_op_line[data-id="'+op_id+'"]').addClass('blink_me');
            //TODO je to tapravi line?
            console.log(op_id);
        },
        check_done: function(){
            var model = this.getParent();
            var self = this;
            var done = true;
            _.each( model.packoplines, function(packopline){
                if (packopline.processed_boolean === "false"){
                    done = false;
                    return done;
                }
            });
            return done;
        },
        get_visible_ids: function(){
            var self = this;
            var visible_op_ids = [];
            var op_ids = this.$('.js_pack_op_line:not(.processed):not(.hidden):not(.container_head):not(.in_container):not(.in_container_hidden)').map(function(){
                return $(this).data('id');
            });
            $.each(op_ids, function(key, op_id){
                visible_op_ids.push(parseInt(op_id));
            });
            return visible_op_ids;
        }
    });


    var PickingCheckingEditorWidget = Widget.extend({
        template: 'PickingCheckingEditorWidget',
        init: function(parent){
            this._super(parent);
            var self = this;
            this.rows = [];
            this.picking_cases = {};
            this.picking_cases = parent.picking_cases;
            this.search_filter = "";
            jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
                return function( elem ) {
                    return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
                };
            });
        },
        get_header: function(){
            return this.getParent().get_header();
        },
        get_location: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;
            _.each(model.locations, function(loc){
                locations.push({name: loc.complete_name, id: loc.id});
            });
            return locations;
        },
        get_picking_cases: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;



            return self.picking_cases;
        },
        goto_pickings_by_case: function(picking_order_id,case_number){
            var self = this;
            // $.bbq.pushState('#action=stock_invoice.pick&picking_order_id='+picking_order_id+'&case_number='+case_number);
            // $(window).trigger('hashchange');
             var model = this.getParent();
             this.$('.oe_pick_app_header').text(model.get_header());
             return model.refresh_ui(parseInt(picking_order_id),parseInt(case_number));
        },

        get_logisticunit: function(){
            var model = this.getParent();
            var ul = [];
            var self = this;
            _.each(model.uls, function(ulog){
                ul.push({name: ulog.name, id: ulog.id});
            });
            return ul;
        },

        validate: function(picking_checking_id){
            var self = this;

            // TODO za checking


            return new Model('stock.checking.validation').call('transfer',[0,picking_checking_id]).then(function(result){
                // if (new_picking_ids) {
                //     // TODO DODAJ CASE
                //     return self.refresh_ui(new_picking_ids[0]);
                // }
                self.getParent().menu();

            });






        },
        validate_all: function(picking_checking_id){
            var self = this;
            // TODO za checking


            return new Model('stock.checking.transfer.all').call('transfer_all',[0,picking_checking_id]).then(function(result){
                // if (new_picking_ids) {
                //     // TODO DODAJ CASE
                //     return self.refresh_ui(new_picking_ids[0]);
                // }
                console.log(result);

                return 0;
            });

            // return new Model('stock.picking.checking').call('validate',[picking_checking_id]).then(function(result){
            //     // if (new_picking_ids) {
            //     //     // TODO DODAJ CASE
            //     //     return self.refresh_ui(new_picking_ids[0]);
            //     // }
            //     console.log(result);
            //
            //     return 0;
            // });


        },

        get_rows: function(){
            var self = this;
            var model = this.getParent();
            this.rows = [];
            var self = this;
            var pack_created = [];



            _.each( model.packoplines, function(packopline){


                var color = "";'';
                //GV
                // if (typeof packopline.product_id[1] !== 'undefined') {
                //     var pack = packopline.package_id[1];
                // }
                // TODO DODAJ PREVERJANJE za picking_invoice_line.qty_done

                if (packopline.product_qty === packopline.qty_done){
                    color = "success ";
                }
                if (packopline.product_qty < packopline.qty_done){
                    color = "danger ";
                }
                //also check that we don't have a line already existing for that package

                // if (typeof packopline.operation_id !== 'undefined'){
                //
                //     self.rows.push({
                //         cols: { product: packopline.product_id[1],
                //             qty: '',
                //             rem: '',
                //             uom: void 0,
                //             lots: void 0,
                //             pack: void 0,
                //             //container: packopline.result_package_id[1],
                //             container_id: void 0,
                //             //to sem spremenil
                //             loc: packopline.location_dest_id[1],
                //             dest: packopline.location_dest_id[1],
                //             id: packopline.id,
                //             product_id: void 0,
                //             can_scan: false,
                //             head_container: true,
                //             //processed_boolean: packopline.processed_boolean,
                //             //package_id: myPackage.id,
                //             //ul_id: myPackage.ul_id[0],
                //             //dest_info_text: packopline.dest_info_text
                //         },
                //         classes: ('success container_head ') + (packopline.processed_boolean === "true"
                //             ? 'processed hidden '
                //             :'')
                //     });
                //     //GV
                //     //pack_created.push(packopline.result_package_id[0]);
                // }
                var lots = _.map(packopline.pack_lot_ids || [], function(id){
                    var op_lot = model.op_lots_index[id];
                    return op_lot.lot_name || op_lot.lot_id[1];
                });
                lots = lots.join(',');


                self.rows.push({
                    cols: { product: packopline.product_id[1],
                        //TODO Gregor qty: packopline.product_qty,
                        qty: packopline.product_qty,
                        rem: packopline.qty_done,
                        //uom: packopline.product_uom_id[1],
                        //lots: lots,
                        //pack: pack,
                        //container: packopline.result_package_id,
                        //container_id: packopline.result_package_id[0],
                        loc: packopline.location_dest_id[1],
                        dest: packopline.location_dest_id[1],
                        id: packopline.id,
                        product_id: packopline.product_id[0],
                        //can_scan: (typeof packopline.result_package_id[1] === 'undefined'),
                        head_container: false,
                        //processed_boolean: packopline.processed_boolean,
                        package_id: void 0,
                        ul_id: -1,
                        procure_method: packopline.procure_method
                        //dest_info_text: packopline.dest_info_text
                    },

                    classes: color+ (packopline.procure_method === 'make_to_stock' ? 'local_stock ':'supplier_stock '),
                });

            });
            //sort element by things to do, then things done, then grouped by packages
            // var group_by_container = _.groupBy(self.rows, function(row){
            //     return row.cols.container;
            // });
            // var sorted_row = [];
            // if (typeof group_by_container.undefined !== 'undefined'){
            //     group_by_container.undefined.sort(function(a,b) {
            //         return (b.classes === '') - (a.classes === '');
            //     });
            //     $.each(group_by_container.undefined, function(key, value){
            //         sorted_row.push(value);
            //     });
            // }
            //
            // $.each(group_by_container, function(key, value){
            //     if (key !== 'undefined'){
            //         $.each(value, function(k,v){
            //             sorted_row.push(v);
            //         });
            //     }
            // });

            return self.rows;
        },
        add_product_to_sale_order: function(partner_id,product_id, quantity) {
            return new Model('stock.picking.checking').call('add_product_to_sale_order', [0, partner_id, product_id, quantity]).then(function (dest_info) {

            })



        },
        renderElement: function(){
            // TODO Tle je bug
            var self = this;

            this._super();
            this.check_content_screen();
            this.$('.js_pick_done').click(function(){
                self.getParent().done();
            });
            this.$('.js_pick_print').click(function(){
                self.getParent().print_picking();
            });
            this.$('.oe_pick_app_header').text(self.get_header());
            this.$('.oe_searchbox').keyup(function(event){
                self.on_searchbox($(this).val());
            });
            this.$('.js_putinpack').click(function(){
                self.getParent().pack();
            });
            //TODO f ja za case done
            this.$('.js_case_done').click(function(){
                self.getParent().case_done();
            });
            this.$('.js_validate_checking').click(function(){

                var picking_checking_id = self.getParent().picking_checking_id;
                self.validate(picking_checking_id);


            });
            this.$('.js_pick_search').click(function(){

                var ean = self.$('.search_cat_number').val();
                var quantity = self.$('.search_cat_quantity').val();

                self.getParent().scan(ean,quantity);
            });

            this.$('.js_validate_all_checking').click(function(){

                var picking_checking_id = self.getParent().picking_checking_id;
                self.validate_all(picking_checking_id);

            });

            this.$('.js_pick_all').click(function(){
                self.getParent().pick_all();
            });
            this.$('.js_drop_down').click(function(){
                self.getParent().drop_down();
            });
            this.$('.js_clear_search').click(function(){
                self.on_searchbox('');
                self.$('.oe_searchbox').val('');
            });
            this.$('.oe_searchbox').focus(function(){
                self.getParent().barcode_off();
            });
            this.$('.oe_searchbox').blur(function(){
                self.getParent().barcode_on();
            });
            this.$('#js_select').change(function(){
                var selection = self.$('#js_select option:selected').attr('value');
                if (selection === "ToDo"){
                    self.getParent().$('.js_pick_pack').removeClass('hidden');
                    self.getParent().$('.js_drop_down').removeClass('hidden');
                    self.$('.js_pack_op_line.processed').addClass('hidden');
                    self.$('.js_pack_op_line:not(.processed)').removeClass('hidden');
                }else{
                    self.getParent().$('.js_pick_pack').addClass('hidden');
                    self.getParent().$('.js_drop_down').addClass('hidden');
                    self.$('.js_pack_op_line.processed').removeClass('hidden');
                    self.$('.js_pack_op_line:not(.processed)').addClass('hidden');
                }
                self.on_searchbox(self.search_filter);
            });
            this.$('.js_plus').click(function(){
                var id = $(this).data('product-id');
                var line_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,line_id,true,'None');
            });
            this.$('.js_minus').click(function(){
                var id = $(this).data('product-id');
                var line_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,line_id,false,'None');
            });
             this.$('.js_go_to_invoice_case').click(function(){
                var case_id = $(this).parents("[data-case-id]:first").data().caseId;
                var picking_order_id = self.getParent().picking_order_id;
                self.goto_pickings_by_case(parseInt(picking_order_id),case_id);

            });


            this.$('.js_unfold').click(function(){
                var op_id = $(this).parent().data('id');
                var line = $(this).parent();
                //select all js_pack_op_line with class in_container_hidden and correct container-id
                var select = self.$('.js_pack_op_line.in_container_hidden[data-container-id=' + op_id + ']');
                if (select.length > 0){
                    //we unfold
                    line.addClass('warning');
                    select.removeClass('in_container_hidden');
                    select.addClass('in_container');
                }else{
                    //we fold
                    line.removeClass('warning');
                    select = self.$('.js_pack_op_line.in_container[data-container-id='+op_id+']');
                    select.removeClass('in_container');
                    select.addClass('in_container_hidden');
                }
            });
            this.$('.js_create_lot').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var lot_name = false;
                self.$('.js_lot_scan').val('');
                var $lot_modal = self.$el.siblings('#js_LotChooseModal');
                //disconnect scanner to prevent scanning a product in the back while dialog is open
                self.getParent().barcode_off();
                $lot_modal.modal();
                //focus input
                $lot_modal.on('shown.bs.modal', function(){
                    self.$('.js_lot_scan').focus();
                });
                //reactivate scanner when dialog close
                $lot_modal.on('hidden.bs.modal', function(){
                    self.getParent().barcode_on();
                });
                self.$('.js_lot_scan').focus();
                //button action
                self.$('.js_validate_lot').click(function(){
                    //get content of input
                    var name = self.$('.js_lot_scan').val();
                    if (name.length !== 0){
                        lot_name = name;
                    }
                    $lot_modal.modal('hide');
                    //we need this here since it is not sure the hide event
                    //will be catch because we refresh the view after the create_lot call

                    self.getParent().barcode_on();
                    self.getParent().create_lot(op_id, lot_name);
                });
            });
            this.$('.js_delete_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().delete_package_op(pack_id);
            });
            this.$('.js_print_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                // $(this).parents("[data-id]:first").data('id')
                self.getParent().print_package(pack_id);
            });
            this.$('.js_submit_value').submit(function(event){
                var id = $(this).parents("[data-id]:first").data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($("input", this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(id, value);
                }
                $("input", this).val("");
                return false;
            });
            this.$('.js_qty').focus(function(){
                self.getParent().barcode_off();
            });
            this.$('.js_qty').blur(function(){
                var id = $(this).parent().parent().children("[data-product-id]:first").data('productId');
                var line_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($(this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(id,line_id, value);
                }
                self.getParent().barcode_on();
            });
            this.$('.js_change_src').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').addClass('source');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_pack_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').addClass('pack');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_add_to_order').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var product_id = $(this).parents("[data-product-id]:first").data('productId');

                self.$('.add_order_quantity').data('product-id',product_id);


                self.$el.siblings('#js_AddtoOrderModal').modal();
            });
            this.$('.js_add_product_to_order').click(function(){

                var select_dom_element = self.$('.add_order_quantity');
                var product_id = select_dom_element.data('product-id');
                // var id = $(this).parent().parent().children("[data-product-id]:first").data('productId');
                // var line_id = $(this).parents("[data-id]:first").data('id');
                var quantity = self.$('.add_order_quantity').val();
                quantity = parseInt(quantity);

                var partner_id = self.getParent().picking_checking.partner_id[0]



                self.$el.siblings('#js_AddtoOrderModal').modal();
                self.add_product_to_sale_order(partner_id,product_id,quantity);
                self.$el.siblings('#js_AddtoOrderModal').modal('hide');
            });
            this.$('.js_validate_location').click(function(){
                //get current selection
                var select_dom_element = self.$('.add_order_quantity');
                var loc_id = self.$('#js_loc_select option:selected').data('loc-id');
                var src_dst = false;
                var op_id = select_dom_element.data('op-id');
                if (select_dom_element.hasClass('pack')){
                    select_dom_element.removeClass('source');
                    var op_ids = [];
                    self.$('.js_pack_op_line[data-container-id='+op_id+']').each(function(){
                        op_ids.push($(this).data('id'));
                    });
                    op_id = op_ids;
                }else if (select_dom_element.hasClass('source')){
                    src_dst = true;
                    select_dom_element.removeClass('source');
                }
                if (loc_id === false){
                    //close window
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                }else{
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                    self.getParent().change_location(op_id, parseInt(loc_id), src_dst);

                }
            });
            this.$('.js_pack_configure').click(function(){
                var pack_id = $(this).parents(".js_pack_op_line:first").data('package-id');
                var ul_id = $(this).parents(".js_pack_op_line:first").data('ulid');
                self.$('#js_packconf_select').val(ul_id);
                self.$('#js_packconf_select').data('pack-id',pack_id);
                self.$el.siblings('#js_PackConfModal').modal();


            });
            this.$('.add_order_quantity').click(function(){
                //get current selection
                var id = $(this).parent().parent().children("[data-product-id]:first").data('productId');
                var line_id = $(this).parents("[data-id]:first").data('id');
                var select_dom_element = self.$('#js_packconf_select');
                // var ul_id = self.$('#js_packconf_select option:selected').data('ul-id');
                var pack_id = select_dom_element.data('pack-id');
                var add_order_quantity  = self.$('.search_cat_quantity').val();

                self.$el.siblings('#js_PackConfModal').modal('hide');
                if (pack_id){
                    self.getParent().set_package_pack(pack_id, ul_id);
                    $('.container_head[data-package-id="'+pack_id+'"]').data('ulid', ul_id);
                }
            });

            //remove navigation bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        on_searchbox: function(query){
            //hide line that has no location matching the query and highlight location that match the query
            this.search_filter = query;
            var processed = ".processed";
            if (this.$('#js_select option:selected').attr('value') === "ToDo"){
                processed = ":not(.processed)";
            }
            if (query !== '') {
                this.$('.js_loc:not(.js_loc:Contains('+query+'))').removeClass('info');
                this.$('.js_loc:Contains('+query+')').addClass('info');
                this.$('.js_pack_op_line'+processed+':not(.js_pack_op_line:has(.js_loc:Contains('+query+')))').addClass('hidden');
                this.$('.js_pack_op_line'+processed+':has(.js_loc:Contains('+query+'))').removeClass('hidden');
            }
            //if no query specified, then show everything
            if (query === '') {
                this.$('.js_loc').removeClass('info');
                this.$('.js_pack_op_line'+processed+'.hidden').removeClass('hidden');
            }
            this.check_content_screen();
        },
        check_content_screen: function(){
            //get all visible element and if none has positive qty, disable put in pack and process button
            var self = this;
            var processed = this.$('.js_pack_op_line.processed');
            var qties = this.$('.js_pack_op_line:not(.processed):not(.hidden) .js_qty').map(function(){
                return $(this).val();
            });
            var container = this.$('.js_pack_op_line.container_head:not(.processed):not(.hidden)');
            var disabled = true;
            $.each(qties,function(index, value){
                if (parseInt(value)>0){
                    disabled = false;
                }
            });

            if (disabled){
                if (container.length===0){
                    self.$('.js_drop_down').addClass('disabled');
                }else{
                    self.$('.js_drop_down').removeClass('disabled');
                }
                self.$('.js_pick_pack').addClass('disabled');
                if (processed.length === 0){
                    self.$('.js_pick_done').addClass('disabled');
                }else{
                    self.$('.js_pick_done').removeClass('disabled');
                }
            }else{
                self.$('.js_drop_down').removeClass('disabled');
                self.$('.js_pick_pack').removeClass('disabled');
                self.$('.js_pick_done').removeClass('disabled');
            }
        },
        get_current_op_selection: function(ignore_container){
            //get ids of visible on the screen
            var pack_op_ids = [];
            this.$('.js_pack_op_line:not(.processed):not(.js_pack_op_line.hidden):not(.container_head)').each(function(){
                var cur_id = $(this).data('id');
                pack_op_ids.push(parseInt(cur_id));
            });
            //get list of element in this.rows where rem > 0 and container is empty is specified
            var list = [];
            _.each(this.rows, function(row){
                if (row.cols.rem > 0 && (ignore_container || typeof row.cols.container === 'undefined' || !row.cols.container)){
                    list.push(row.cols.id);
                }
            });
            //return only those visible with rem qty > 0 and container empty
            return _.intersection(pack_op_ids, list);
        },
        remove_blink: function(){
            this.$('.js_pack_op_line.blink_me').removeClass('blink_me');
        },
        blink: function(op_id){
            this.$('.js_pack_op_line[data-id="'+op_id+'"]').addClass('blink_me');
            //TODO je to tapravi line?
            console.log(op_id);
        },
        check_done: function(){
            var model = this.getParent();
            var self = this;
            var done = true;
            _.each( model.packoplines, function(packopline){
                if (packopline.processed_boolean === "false"){
                    done = false;
                    return done;
                }
            });
            return done;
        },
        get_visible_ids: function(){
            var self = this;
            var visible_op_ids = [];
            var op_ids = this.$('.js_pack_op_line:not(.processed):not(.hidden):not(.container_head):not(.in_container):not(.in_container_hidden)').map(function(){
                return $(this).data('id');
            });
            $.each(op_ids, function(key, op_id){
                visible_op_ids.push(parseInt(op_id));
            });
            return visible_op_ids;
        }
    });


    var PickingCaseWidget = MobileWidget.extend({
        template: 'PickingCaseWidget',
        init: function(parent, params){
            this._super(parent,params);
            var self = this;
            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "stock_invoice.menu"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.menu',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "stock_invoice.pick"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.pick',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }

            });

            var init_hash = $.bbq.getState();
            this.picking_order_id = init_hash.picking_order_id
                ? init_hash.picking_order_id
                : void 0;
            this.picking_invoices = [];
            this.picking_lines = [];
            this.picking_cases = {};
            this.scanning_type = 0;
            this.picking_invoice_lines = {};
            this.pickings_by_invoice = {};
            this.pickings_by_id = {};
            this.picking_search_string = "";

            if(this.picking_order_id){
                this.loaded = this.load(this.picking_order_id);
            }
        },
        load: function(picking_order_id){
            var self = this;
            return new Model('picking.invoice').call('process_picking_invoice',[parseInt(picking_order_id)]).
            then(function(result) {
                if (result){
                    return new Model('picking.invoice.line').call('search_read', [[['picking_order_id', "=", parseInt(picking_order_id)]]]).then(function (picking_invoice_lines) {

                        self.picking_invoice_lines = picking_invoice_lines;
                        var invoices_ids = [];
                        '';
                        for (var i = 0; i < picking_invoice_lines.length; i++) {
                            //TODO preveri ce ima case vse line done alid draft
                            var data_values = picking_invoice_lines[i];
                            var case_number = data_values['case_number'];

                            if (!(case_number in self.picking_cases)) {
                                self.picking_cases[case_number] = [];
                            }
                            self.picking_cases[case_number].push(data_values);
                        }

                        var state = 'done';
                        var status = false;

                        var picking_cases = self.picking_cases;

                        for (var key in picking_cases) {
                            for (var line_key in picking_cases[key]) {
                                console.log(picking_cases[key][line_key]);
                                if (picking_cases[key][line_key].qty_done !== picking_cases[key][line_key].qty) {
                                    state = 'draft';
                                }

                                if (picking_cases[key][line_key].is_done) {
                                    status = true;
                                }
                            }
                            picking_cases[key].status = status;
                            picking_cases[key].state = state;
                        }

                        self.picking_cases = picking_cases;
                        return self.picking_cases;

                    }).then(function (picking_cases) {


                        for (var key in picking_cases) {

                            self.pickings_by_id[key] = key;
                            self.picking_search_string += String(key) + ':' + (key) + '\n';
                            //TODO


                        }
                        self.picking_cases = picking_cases;

                    });
                }
            });
        },
        validate: function(picking_order_id){
            var self = this;

            return new Model('picking.invoice.validation').call('transfer_from_ui',[0,picking_order_id]).then(function(new_picking_ids){
                // if (new_picking_ids) {
                //     // TODO DODAJ CASE
                //     return self.refresh_ui(new_picking_ids[0]);
                // }
                console.log(picking_order_id);

                return 0;
            });



            // return new Model('stock.picking').
            // call('action_done_from_ui',[self.picking.id, self.picking_type_id]).
            // then(function(new_picking_ids){
            //     if (new_picking_ids) {
            //         // TODO DODAJ CASE
            //         return self.refresh_ui(new_picking_ids[0]);
            //     }
            //     return 0;
            // });
        },
        menu: function(){
            $.bbq.pushState('#action=stock_invoice.menu');
            $(window).trigger('hashchange');
        },


        renderElement: function(){
            this._super();
            var self = this;
            this.$('.js_go_to_invoice_case').click(function(){
                var case_id = $(this).parents("[data-case-id]:first").data().caseId;
                self.goto_pickings_by_case(case_id);
            });

            this.$('.js_pick_quit').click(function(){
                self.quit();
            });
            this.$('.js_validate_invoice').click(function(){
                self.validate(self.picking_order_id);
            });

            this.$('.js_pick_scan').click(function(){
                self.scan_picking($(this).data('id'));
            });
            this.$('.js_pick_last').click(function(){
                self.goto_last_picking_of_type($(this).data('id'));
            });
            this.$('.oe_searchbox').keyup(function(event){
                self.on_searchbox($(this).val());
            });
            this.$('.js_pick_menu').click(function(){
                self.menu();
            });
            //remove navigation bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        barcode_on: function(){
            if (this.is_barcode_on) {
                return;
            }
            this.is_barcode_on = true;
            core.bus.on('barcode_scanned', this, this._barcode_handler);
        },
        barcode_off: function(){
            this.is_barcode_on = false;
            core.bus.off('barcode_scanned', this, this._barcode_handler);
        },
        _barcode_handler: function(barcode){
            this.on_scan(barcode);
        },
        start: function(){
            this._super();
            var self = this;
            //web_client.set_content_full_screen(true);
            self.barcode_on();
            this.loaded.then(function(){
                self.renderElement();
            });
        },
        goto_pickings_by_case: function(case_number){

            $.bbq.pushState('#action=stock_invoice.pick&picking_order_id='+this.picking_order_id+'&case_number='+case_number);
            $(window).trigger('hashchange');

        },
        goto_picking: function(picking_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_id='+picking_id);
            $(window).trigger('hashchange');
        },

        goto_last_picking_of_type: function(type_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_type_id='+type_id);
            $(window).trigger('hashchange');
        },
        search_picking: function(barcode){
            try {
                var re = new RegExp("([0-9]+):.*?"+barcode.toUpperCase(),"gi");
            } catch(e) {
                //avoid crash if a not supported char is given (like '\' or ')')
                return [];
            }

            var results = [];
            for(var i = 0; i < 100; i++){
                var r = re.exec(this.picking_search_string);
                if(r){
                    var picking = this.pickings_by_id[Number(r[1])];
                    if(picking){
                        results.push(picking);
                    }
                }else{
                    break;
                }
            }
            return results;
        },
        on_scan: function(barcode){
            //OB SKENIRANJU POJDI NA PRAVI INVOICE
            var self = this;
            //barcode = 684;


            if (self.picking_cases.hasOwnProperty(barcode)){
                this.goto_pickings_by_case(barcode);
            }
            this.$('.js_picking_not_found').removeClass('hidden');
            //TODO dodaj opozorilo ce ni pravi picking
            clearTimeout(this.picking_not_found_timeout);
            this.picking_not_found_timeout = setTimeout(function(){
                self.$('.js_picking_not_found').addClass('hidden');
            },2000);



        },
        on_searchbox: function(query){
            var self = this;

            clearTimeout(this.searchbox_timeout);
            this.searchbox_timout = setTimeout(function(){
                if(query){
                    self.$('.js_picking_not_found').addClass('hidden');
                    self.$('.js_picking_categories').addClass('hidden');
                    self.$('.js_picking_search_results').html(
                        qweb.render('CaseSearchResults',{results:self.search_picking(query)})
                    );
                    self.$('.js_picking_search_results .oe_picking').click(function(){
                        self.goto_pickings_by_case($(this).data('id') );
                    });
                    self.$('.js_picking_search_results').removeClass('hidden');
                }else{
                    self.$('.js_title_label').removeClass('hidden');
                    self.$('.js_picking_categories').removeClass('hidden');
                    self.$('.js_picking_search_results').addClass('hidden');
                }
            },100);
        },
        quit: function(){
            return new Model("ir.model.data").call("search_read", [[['name', '=', 'stock_picking_type_action']], ['res_id']]).then(function(res) {
                window.location = '/web#action=' + res[0].res_id;
            });
        },
        destroy: function(){
            this._super();
            this.barcode_off();
            //web_client.set_content_full_screen(false);
        }
    });
    core.action_registry.add('picking_case.case', PickingCaseWidget);


    //END CASE


    //PICKING INVOICE MENU
    var PickingMenuInvoiceWidget = MobileWidget.extend({
        template: 'PickingMenuInvoiceWidget',
        init: function(parent, params){
            this._super(parent,params);
            var self = this;
            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "stock_invoice.menu"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.menu',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_case.case"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_case.case',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "stock_invoice.pick"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.pick',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "stock.ui"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock.ui',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_checking.partner"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.partner',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_checking.checking"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.checking',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }

            });

            this.picking_invoices = [];
            this.loaded = this.load();
            this.scanning_type = 0;
            this.pickings_by_invoice = {};
            this.pickings_by_id = {};
            this.picking_search_string = "";
        },
        load: function(){
            var self = this;

            return new Model('picking.invoice').call('search_read', [[]]).
            then(function(invoices){

                self.picking_invoices = invoices;
                var invoices_ids = [];
                for(var i = 0; i < invoices.length; i++){
                    self.pickings_by_invoice[invoices[i].id] = [];
                    invoices_ids.push(invoices[i].id);
                }
                self.pickings_by_invoice[0] = [];

                return new Model('picking.invoice').call('search_read',
                    [],
                    {context: new data.CompoundContext()}
                );

            }).then(function(pickings){
                self.pickings = pickings;
                for(var i = 0; i < pickings.length; i++){
                    var picking = pickings[i];
                    // self.pickings_by_invoice[picking.picking_type_id[0]].push(picking);
                    self.pickings_by_id[picking.id] = picking;
                    self.picking_search_string += String(picking.id) + ':' + (picking.invoice_no
                        ? picking.name.toUpperCase()
                        : '') + '\n';
                }

            });
        },
        renderElement: function(){
            this._super();
            var self = this;
            this.$('.js_pick_quit').click(function(){
                self.quit();
            });
            this.$('.js_pick_scan').click(function(){
                self.scan_picking($(this).data('id'));
            });
            this.$('.js_pick_last').click(function(){
                self.goto_last_picking_of_type($(this).data('id'));
            });
            this.$('.oe_searchbox').keyup(function(event){
                self.on_searchbox($(this).val());
            });
            this.$('.js_go_to_pick_invoice').click(function(){
                var invoice_id = $(this).parents("[data-id]:first").data('id');
                self.goto_invoice_case_picking(invoice_id);
            });


            //remove navigation bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        barcode_on: function(){
            if (this.is_barcode_on) {
                return;
            }
            this.is_barcode_on = true;
            core.bus.on('barcode_scanned', this, this._barcode_handler);
        },
        barcode_off: function(){
            this.is_barcode_on = false;
            core.bus.off('barcode_scanned', this, this._barcode_handler);
        },
        _barcode_handler: function(barcode){
            this.on_scan(barcode);
        },
        start: function(){
            this._super();
            var self = this;
            //web_client.set_content_full_screen(true);
            self.barcode_on();
            this.loaded.then(function(){
                self.renderElement();
            });
        },
        goto_invoice_case_picking: function(picking_id){
            $.bbq.pushState('#action=picking_case.case&picking_order_id='+picking_id);
            $(window).trigger('hashchange');
        },
        goto_picking: function(picking_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_id='+picking_id);
            $(window).trigger('hashchange');
        },
        goto_last_picking_of_type: function(type_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_type_id='+type_id);
            $(window).trigger('hashchange');
        },
        search_picking: function(barcode){
            try {
                var re = new RegExp("([0-9]+):.*?"+barcode.toUpperCase(),"gi");
            } catch(e) {
                //avoid crash if a not supported char is given (like '\' or ')')
                return [];
            }

            var results = [];
            for(var i = 0; i < 100; i++){
                var r = re.exec(this.picking_search_string);
                if(r){
                    var picking = this.pickings_by_id[Number(r[1])];
                    if(picking){
                        results.push(picking);
                    }
                }else{
                    break;
                }
            }
            return results;
        },
        on_scan: function(barcode){
            //OB SKENIRANJU POJDI NA PRAVI INVOICE
            var self = this;


            for(var i = 0, len = this.picking_invoices.length; i < len; i++){
                var picking = this.picking_invoices[i];
                //testing
                //barcode = 584227;
                if(picking.invoice_no === barcode){

                    this.goto_invoice_case_picking(picking.id);
                    break;
                }
            }
            this.$('.js_picking_not_found').removeClass('hidden');

            clearTimeout(this.picking_not_found_timeout);
            this.picking_not_found_timeout = setTimeout(function(){
                self.$('.js_picking_not_found').addClass('hidden');
            },2000);

        },
        on_searchbox: function(query){
            var self = this;

            clearTimeout(this.searchbox_timeout);
            this.searchbox_timout = setTimeout(function(){
                if(query){
                    self.$('.js_picking_not_found').addClass('hidden');
                    self.$('.js_picking_categories').addClass('hidden');
                    self.$('.js_picking_search_results').html(
                        qweb.render('PickingSearchResults',{results:self.search_picking(query)})
                    );
                    self.$('.js_picking_search_results .oe_picking').click(function(){
                        self.goto_invoice_case_picking($(this).data('id'));
                    });
                    self.$('.js_picking_search_results').removeClass('hidden');
                }else{
                    self.$('.js_title_label').removeClass('hidden');
                    self.$('.js_picking_categories').removeClass('hidden');
                    self.$('.js_picking_search_results').addClass('hidden');
                }
            },100);
        },
        quit: function(){
            return new Model("ir.model.data").call("search_read", [[['name', '=', 'stock_picking_type_action']], ['res_id']]).then(function(res) {
                window.location = '/web#action=' + res[0].res_id;
            });
        },
        destroy: function(){
            this._super();
            this.barcode_off();
            //web_client.set_content_full_screen(false);
        }
    });
    core.action_registry.add('stock_invoice.menu', PickingMenuInvoiceWidget);

    // INVOICE PICKING
    var InvoicePickingWidget = MobileWidget.extend({
        template: 'InvoicePickingWidget',
        init: function(parent,params){
            this._super(parent,params);
            var self = this;
            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "stock_invoice.menu"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.menu',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_checking.partner"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.partner',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }

            });
            var init_hash = $.bbq.getState();
            this.last_pick_ean = {};
            this.picking_cases = {};
            this.pickings_by_id = {};
            this.picking_search_string = "";
            this.picking_order_id = init_hash.picking_order_id
                ? init_hash.picking_order_id
                : void 0;
            this.case_number = init_hash.case_number
                ? init_hash.case_number
                : void 0;
            this.picking = null;
            this.pickings = [];
            this.packoplines = null;
            this.selected_operation = { id: null, picking_order_id: null };
            this.packages = null;
            this.locations = [];
            this.uls = [];
            if(this.picking_order_id && this.case_number){
                this.loaded = this.load(this.picking_order_id,this.case_number);
            }else{
                this.loaded = this.load();
            }

        },
        get_new_qty: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].qty;
                }


            }
            return null;

        },
        get_new_qty_done: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].qty_done;
                }


            }
            return null;

        },
        get_new_dest_info: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].dest_info_text;
                }


            }
            return null;

        },
        get_picking_cases: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;
            var model = this.getParent();
            var pickings = {};
            pickings = model.__parentedChildren[1].picking_cases;


            return pickings;
        },


        // load the picking data from the server. If picking_id is undefined, it will take the first picking
        // belonging to the category
        load: function(picking_order_id,case_number){
            var self = this;
            var model = this.getParent();
            if (Object.keys(self.picking_cases).length == 0){
                this.picking_cases = model.__parentedChildren[1].picking_cases;

            }
            else{
                this.picking_cases = self.picking_cases;
            }


            function load_picking_list(picking_order_id){
                var pickings = new $.Deferred();
                new Model('picking.invoice.line').
                call(
                    'get_next_picking_for_ui',
                    [], { picking_order_id : parseInt(picking_order_id)}
                ).then(function(picking_invoice_lines){
                    if(!picking_invoice_lines || picking_invoice_lines.length === 0){
                        (new Dialog(self,{
                            title: _t('No Picking Available'),
                            buttons: [{
                                text:_t('Ok'),
                                click: function(){
                                    self.menu();
                                }
                            }]
                        }, _t('<p>We could not find a picking to display.</p>'))).open();

                        pickings.reject();
                    }else{
                        self.pickings = picking_invoice_lines;
                        pickings.resolve(picking_invoice_lines);
                    }
                });

                return pickings;
            }

            // if we have a specified picking id, we load that one, and we load the picking of the same type as the active list
            if( picking_order_id && case_number){
                var loaded_picking = new Model('picking.invoice').call('search_read',[[['id','=',picking_order_id]]]).

                then(function(picking){
                    self.picking = picking[0];

                    // self.picking_type_id = picking[0].picking_type_id[0];
                    return load_picking_list(self.picking.id);
                });
                // var loaded_picking = new Model('stock.picking').
                //     call('read',[[parseInt(picking_id)], []], {context:new data.CompoundContext()}).
                //     then(function(picking){
                //         self.picking = picking[0];
                //         self.picking_type_id = picking[0].picking_type_id[0];
                //         return load_picking_list(self.picking.picking_type_id[0]);
                //     });
            }else{
                // if we don't have a specified picking id, we load the pickings belong to the specified type, and then we take
                // the first one of that list as the active picking
                loaded_picking = new $.Deferred();
                load_picking_list(self.picking.id).
                then(function(){
                    return new Model('stock.picking').call('read',[self.pickings[0],[]], {context:new data.CompoundContext()});
                }).then(function(picking){
                    self.picking = picking[0];
                    // self.picking_type_id = picking[0].picking_type_id[0];
                    loaded_picking.resolve();
                });
            }

            return loaded_picking.then(function(){
                if (!_.isEmpty(self.locations)){
                    return $.when();
                }
                return new Model('stock.location').call('search',[[['usage','=','internal']]]).then(function(locations_ids){
                    return new Model('stock.location').call('read',[locations_ids, []]).then(function(locations){
                        self.locations = locations;
                    });
                });
            }).then(function(){
                return new Model('stock.picking').call('check_group_pack').then(function(result){
                    return (self.show_pack = result);
                });
            }).then(function(){
                return new Model('stock.picking').call('check_group_lot').then(function(result){
                    return (self.show_lot = result);
                });
            }).then(function(){
                return new Model('picking.invoice.line').call('search_read',[[['picking_order_id',"=",parseInt(picking_order_id)],['case_number',"=",parseInt(case_number)]]]).
                then(function(picking_invoice_lines){

                    var pack_operations_ids = [];
                    for(var i = 0; i < picking_invoice_lines.length; i++){
                        var real_test = '';
                        if(picking_invoice_lines[i].pack_operation_product[0]){
                            //TODO Ignore tistega kateri ni prevzet, ce je done
                                pack_operations_ids.push(picking_invoice_lines[i].pack_operation_product[0]);



                        }


                    }
                    self.picking_invoice_lines = picking_invoice_lines;
                    return pack_operations_ids;

                });



            }).then(function(pack_op_ids){
                return new Model('stock.pack.operation').call('read',[pack_op_ids, []], {context:new data.CompoundContext()});
            }).then(function(operations){
                // TODO: find operations by invoice picking
                self.packoplines = operations;
                var package_ids = [];
                self.lot_ids = [];

                //TODO dodaj kolicino od self.picking_invoice_lines
                for(var i = 0; i < operations.length; i++){
                    if(!_.contains(package_ids,operations[i].result_package_id[0])){
                        var new_qty = self.get_new_qty(operations[i].id);
                        if (new_qty != null){
                            operations[i].product_qty = new_qty;
                        }

                        var new_qty_done = self.get_new_qty_done(operations[i].id);
                        if (new_qty_done != null){
                            operations[i].qty_done = new_qty_done;
                        }
                        var new_dest_info = self.get_new_dest_info(operations[i].id);
                        if (new_dest_info != null){
                            operations[i].dest_info_text = new_dest_info;
                        }



                        if (operations[i].pack_lot_ids.length) {
                            self.lot_ids = self.lot_ids.concat(operations[i].pack_lot_ids);
                        }
                        if (operations[i].result_package_id[0]){
                            package_ids.push(operations[i].result_package_id[0].id);
                        }
                    }
                }
                return new Model('stock.quant.package').call('read',[package_ids, []], {context:new data.CompoundContext()});
            }).then(function(packages){
                self.packages = packages;
                return new Model('stock.pack.operation.lot').call('read',[self.lot_ids, []], {context:new data.CompoundContext()});
            }).then(function(op_lots){
                self.op_lots_index = {};
                _.each(op_lots, function(item){
                    self.op_lots_index[item.id] = item;
                });
            });
        },
        barcode_on: function(){
            if (this.is_barcode_on) {
                return;
            }
            this.is_barcode_on = true;
            core.bus.on('barcode_scanned', this, this._barcode_handler);
        },
        barcode_off: function(){
            this.is_barcode_on = false;
            core.bus.off('barcode_scanned', this, this._barcode_handler);
        },
        _barcode_handler: function(barcode){
            this.scan(barcode,'None');
        },
        start: function(){
            this._super();
            var self = this;
            //web_client.set_content_full_screen(true);
            self.barcode_on();
            this.$('.js_pick_quit').click(function () {
                self.quit();
            });
            this.$('.js_pick_prev').click(function(){
                self.picking_prev();
            });
            this.$('.js_pick_next').click(function(){
                self.picking_next();
            });
            this.$('.js_pick_menu').click(function(){
                self.menu();
            });
            //TODO Izbor Paketov
            this.$('.js_pick_case').click(function(){
                self.case_pick();
            });

            this.$('.js_reload_op').click(function(){
                self.reload_pack_operation();
            });
            this.$('.js_pick_search').click(function(){
                console.log("tle sem 2");
            });

            $.when(this.loaded).done(function(){
                self.picking_editor = new PickingEditorWidget(self);
                self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));

                if( self.picking.id === self.pickings[0]){
                    self.$('.js_pick_prev').addClass('disabled');
                }else{
                    self.$('.js_pick_prev').removeClass('disabled');
                }

                if( self.picking.id === self.pickings[self.pickings.length-1] ){
                    self.$('.js_pick_next').addClass('disabled');
                }else{
                    self.$('.js_pick_next').removeClass('disabled');
                }
                // if (self.picking.recompute_pack_op){
                //     self.$('.oe_reload_op').removeClass('hidden');
                // }else {
                //     self.$('.oe_reload_op').addClass('hidden');
                // }
                // TODO Gregor
                self.$('.oe_reload_op').addClass('hidden');
                if (!self.show_pack){
                    self.$('.js_pick_pack').addClass('hidden');
                }
                if (!self.show_lot){
                    self.$('.js_create_lot').addClass('hidden');
                }

            }).fail(function(error) {
                console.log(error);
            });

        },
        on_searchbox: function(query){
            var self = this;
            // self.picking_editor.on_searchbox(query.toUpperCase());
            self.picking_editor.on_searchbox(query);
        },
        // reloads the data from the provided picking and refresh the ui.
        // (if no picking_id is provided, gets the first picking in the db)
        refresh_ui: function(picking_id,case_number){
            var self = this;
            var remove_search_filter = "";
            if (parseInt(self.picking_order_id) === parseInt(picking_id) && parseInt(self.case_number) === parseInt(case_number)){
                remove_search_filter = self.$('.oe_searchbox').val();
            }
            return this.load(picking_id,case_number).
            then(function(){
                self.picking_editor.remove_blink();
                self.picking_editor.renderElement();
                // if (!self.show_pack){
                //     self.$('.js_pick_pack').addClass('hidden');
                // }
                // if (!self.show_lot){
                //     self.$('.js_create_lot').addClass('hidden');
                // }
                // if (self.picking.recompute_pack_op){
                //     self.$('.oe_reload_op').removeClass('hidden');
                // }else {
                //     self.$('.oe_reload_op').addClass('hidden');
                // }
                //GV
                // if( self.picking.id === self.pickings[0]){
                //     self.$('.js_pick_prev').addClass('disabled');
                // }else{
                //     self.$('.js_pick_prev').removeClass('disabled');
                // }
                //
                // if( self.picking.id === self.pickings[self.pickings.length-1] ){
                //     self.$('.js_pick_next').addClass('disabled');
                // }else{
                //     self.$('.js_pick_next').removeClass('disabled');
                // }
                if (remove_search_filter === ""){
                    self.$('.oe_searchbox').val('');
                    self.on_searchbox('');
                }else{
                    self.$('.oe_searchbox').val(remove_search_filter);
                    self.on_searchbox(remove_search_filter);
                }
            });
        },
        get_header: function(){
            result = '';
            if(this.picking){

                var result = "Faktura: "+this.picking.name +" Paket: "+this.case_number;
                return result;
            }
            return result;
        },
        menu: function(){
            $.bbq.pushState('#action=stock_invoice.menu');
            $(window).trigger('hashchange');
        },
        case_pick: function(){

            $.bbq.pushState('#action=picking_case.case&picking_order_id='+this.picking_order_id);

            $(window).trigger('hashchange');
        },
        scan: function(ean, quantity){
            //ean = '0FRACCD02005';

            var self = this;

            if (quantity == 'None'){
                quantity = 'None';
            }
            else{
                quantity = parseInt(quantity)
            }

            if (ean.length == 12){
                this.last_pick_ean = ean;
            }
            if (ean.length == 4){
                quantity = parseInt(ean);
                ean = this.last_pick_ean;

            }
            //call('process_product_id_from_ui', [0,parseInt(self.picking_order_id),parseInt(self.case_number),false,ean]).
            var product_visible_ids = this.picking_editor.get_visible_ids();
            return new Model('picking.invoice.line').
            call('process_product_id_from_ui', [0,parseInt(self.picking_order_id),parseInt(self.case_number),false,ean,true,quantity]).
            then(function(dest_info){
                // if (result.filter_loc !== false){
                //     //check if we have receive a location as answer
                //     if (typeof result.filter_loc !== 'undefined'){
                //         var modal_loc_hidden = self.$('#js_LocationChooseModal').attr('aria-hidden');
                //         if (modal_loc_hidden === "false"){
                //             self.$('#js_LocationChooseModal .js_loc_option[data-loc-id='+result.filter_loc_id+']').attr('selected','selected');
                //         }else{
                //             self.$('.oe_searchbox').val(result.filter_loc);
                //             self.on_searchbox(result.filter_loc);
                //         }
                //     }
                // }


                //TODO izpis trenutnega pickinga
                if (dest_info === false){

                    self.$('.js_picking_not_found').removeClass('hidden');


                    //TODO dodaj opozorilo ce ni pravi picking
                    clearTimeout(this.picking_not_found_timeout);
                    this.picking_not_found_timeout = setTimeout(function(){
                           self.$('.js_picking_not_found').addClass('hidden');
                     },5000000);
                }

                if (dest_info != ""){
                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').html(dest_info);
                    self.$('.oe_pick_dest_info').removeClass('hidden');

                }


                else{


                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').addClass('hidden');
                }


                setTimeout(function(){
                    self.refresh_ui(self.picking.id,parseInt(self.case_number));
                },5000);

                // self.refresh_ui(self.picking.id,parseInt(self.case_number)).then(function(){
                //     return self.picking_editor.blink(result.operation_id);
                // });

            });
        },
        scan_product_id: function(product_id,increment,quantity) {
            var self = this;
            // return new Model('picking.invoice.line').
            // call('process_product_id_from_ui', [self.picking.id, product_id, op_id, increment]).
            // then(function(result){
            //     // TODO DODAJ destination info
            //     return self.refresh_ui(self.picking.id,self.case_number);
            //     //return self.refresh_ui(self.picking.id);
            // });




            //TODO popravi da ne bo fix na [0]
            return new Model('picking.invoice.line').
            call('process_product_id_from_ui', [0,parseInt(self.picking_order_id),parseInt(self.case_number),product_id,false,increment,quantity]).
            then(function(dest_info){
                // TODO iskanje pravega dest_info

                if (dest_info != "" || dest_info != ' <br/>'){
                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').html(dest_info);
                    self.$('.oe_pick_dest_info').removeClass('hidden');

                }


                else{


                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').addClass('hidden');
                }

                return self.refresh_ui(self.picking.id,self.case_number);
                //return self.refresh_ui(self.picking.id);
            });


        },
        pack: function(){
            var self = this;
            var pack_op_ids = self.picking_editor.get_current_op_selection(false);
            if (pack_op_ids.length !== 0){
                return new Model('stock.picking').
                call('put_in_pack', [[self.picking.id]]).
                then(function(pack){
                    //TODO: the functionality using current_package_id in context is not needed anymore
                    session.user_context.current_package_id = false;
                    // TODO DODAJ CASE
                    return self.refresh_ui(self.picking.id);
                });
            }
        },
        case_done: function(){
            var self = this;
            if (self.case_number){
                self.picking_cases[self.case_number].state = 'done';
            }



            // var pack_op_ids = self.picking_editor.get_current_op_selection(false);
            // if (pack_op_ids.length !== 0){
            //     return new Model('stock.picking').
            //     call('put_in_pack', [[self.picking.id]]).
            //     then(function(pack){
            //         //TODO: the functionality using current_package_id in context is not needed anymore
            //         session.user_context.current_package_id = false;
            //         // TODO DODAJ CASE
            //         return self.refresh_ui(self.picking.id);
            //     });
            // }
            //return self.refresh_ui(self.picking.id);
            return self.refresh_ui(parseInt(self.picking_order_id),parseInt(self.case_number));
        },
        pick_all: function(){
            var self = this;

            for(var i = 0; i < this.packoplines.length; i++){
                self.scan_product_id(this.packoplines[i].product_id[0],false,this.packoplines[i].product_qty);

            }



            //
            return self.refresh_ui(parseInt(self.picking_order_id),parseInt(self.case_number));
        },
        drop_down: function(){
            var self = this;
            var pack_op_ids = self.picking_editor.get_current_op_selection(true);
            if (pack_op_ids.length !== 0){
                var backorder_model = new Model('stock.backorder.confirmation');
                return backorder_model.call('create', [{'pick_id': self.picking.id}]).then(function(id){
                    return backorder_model.call('process', [id]).then(function(){
                        // TODO DODAJ CASE
                        return self.refresh_ui(self.picking.id).then(function(){
                            if (self.picking_editor.check_done()){
                                return self.done();
                            }
                        });
                    });
                });
            }
        },
        done: function(){
            var self = this;
            return new Model('stock.picking').
            call('action_done_from_ui',[self.picking.id, self.picking_type_id]).
            then(function(new_picking_ids){
                if (new_picking_ids) {
                    // TODO DODAJ CASE
                    return self.refresh_ui(new_picking_ids[0]);
                }
                return 0;
            });
        },
        create_lot: function(op_id, lot_name){
            var self = this;
            return new Model('stock.pack.operation').
            call('create_and_assign_lot',[parseInt(op_id), lot_name]).
            then(function(){
                // TODO DODAJ CASE
                return self.refresh_ui(self.picking.id);
            });
        },
        change_location: function(op_id, loc_id, is_src_dst){
            var self = this;
            var vals = {'location_dest_id': loc_id};
            if (is_src_dst){
                vals = {'location_id': loc_id};
            }
            return new Model('stock.pack.operation').
            call('write',[op_id, vals]).
            then(function(){
                // TODO DODAJ CASE
                return self.refresh_ui(self.picking.id);
            });
        },
        print_package: function(package_id){
            var self = this;
            return new Model('stock.quant.package').
            call('action_print',[[package_id]]).
            then(function(action){
                return self.do_action(action);
            });
        },
        print_picking: function(){
            var self = this;
            return new Model('stock.picking.type').call('read', [[self.picking_type_id], ['code']], {context:new data.CompoundContext()}).
            then(function(pick_type){
                return new Model('stock.picking').call('do_print_picking',[[self.picking.id]]).
                then(function(action){
                    return self.do_action(action);
                });
            });
        },
        picking_next: function(){
            for(var i = 0; i < this.pickings.length; i++){
                if (parseInt(this.pickings[i]) === parseInt(this.case_number)){
                    if(i+1 >= this.pickings.length){
                        this.case_number = parseInt(this.pickings[0]);
                        this.refresh_ui(parseInt(this.picking_order_id),parseInt(this.pickings[0]));
                        break;
                    }
                    else{
                        this.case_number = parseInt(this.pickings[i+1]);
                        this.refresh_ui(parseInt(this.picking_order_id), parseInt(this.pickings[i+1]));
                        break;
                    }
                }
            }
        },
        picking_prev: function(){
            for(var i = 0; i < this.pickings.length; i++){
                if (parseInt(this.pickings[i]) === parseInt(this.case_number)){
                    if(i === 0 ){
                        this.case_number = parseInt(this.pickings[this.pickings.length - 1]);
                        this.refresh_ui(this.picking_order_id,this.pickings[this.pickings.length - 1]);
                        break;
                    }
                    else{
                        this.case_number = parseInt(this.pickings[i-1]);
                        this.refresh_ui(this.picking_order_id, this.pickings[i-1]);
                        break;
                    }
                }
            }
        },
        delete_package_op: function(pack_id){
            var self = this;
            return new Model('stock.pack.operation').call('search', [[['result_package_id', '=', pack_id]]]).
            then(function(op_ids) {
                return new Model('stock.pack.operation').call('write', [op_ids, {'result_package_id':false}]).
                then(function() {
                    // TODO DODAJ CASE
                    return self.refresh_ui(self.picking.id);
                });
            });
        },
        set_operation_quantity: function(product_id, quantity){
            var self = this;
            if(quantity >= 0){
                // TODO Spremeni funkcijo ...tako k da kliknes na increment


                self.scan_product_id(product_id,false,quantity);

                // return new Model('stock.pack.operation').
                // call('write',[[op_id],{'qty_done': quantity }]).
                // then(function(){
                //
                //     self.refresh_ui(self.picking.id);
                // });
            }
        },
        set_package_pack: function(package_id, pack){
            var self = this;
            return new Model('stock.quant.package').
            call('write',[[package_id],{'ul_id': pack }]);
        },
        reload_pack_operation: function(){
            var self = this;
            return new Model('stock.picking').
            call('do_prepare_partial',[[self.picking.id]]).
            then(function(){

                // TODO DODAJ CASE
                self.refresh_ui(self.picking.id);
            });
        },
        quit: function(){
            this.destroy();
            return new Model("ir.model.data").call("search_read", [[['name', '=', 'stock_picking_type_action']], ['res_id']]).then(function(res) {
                window.location = '/web#action=' + res[0].res_id;
            });
        },
        destroy: function(){
            this._super();
            //web_client.set_content_full_screen(false);
            this.barcode_off();
        }
    });
    core.action_registry.add('stock_invoice.pick', InvoicePickingWidget);









    var PickingCheckingPartnerWidget = MobileWidget.extend({
        template: 'PickingCheckingPartnerWidget',
        init: function(parent, params){
            this._super(parent,params);
            var self = this;

            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "picking_checking.partner"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.partner',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_checking.checking"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.checking',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }

            });

            var init_hash = $.bbq.getState();
            this.picking_order_id = init_hash.picking_order_id
                ? init_hash.picking_order_id
                : void 0;
            this.picking_invoices = [];
            this.picking_lines = [];
            this.picking_cases = {};
            this.scanning_type = 0;
            this.picking_invoice_lines = {};
            this.pickings_by_invoice = {};
            this.pickings_by_id = {};
            this.picking_search_string = "";
            this.picking_checking = {};

            this.loaded = this.load();

        },
        load: function(){
            var self = this;



            return new Model('stock.picking.type').call('new_sort_and_create',[[]]).then(function(result) {
                if (result){

                    return new Model('stock.picking.checking').call('search_read',[[]]).
                    then(function(picking_checking_objects) {
                        if (picking_checking_objects) {
                            for (var i = 0; i < picking_checking_objects.length; i++) {
                                if (!(picking_checking_objects[i].id.toString() in self.picking_checking)) {
                                    self.picking_checking[picking_checking_objects[i].id.toString()] = picking_checking_objects[i];
                                    self.picking_search_string += String(picking_checking_objects[i].id.toString()) + ':' + (picking_checking_objects[i].partner_id[1].toString()) + '\n';
                                    self.pickings_by_id[picking_checking_objects[i].id.toString()] = picking_checking_objects[i].partner_id[1].toString();
                                }

                            }
                        }
                    });
                }
            });

        },
        validate: function(picking_order_id){
            var self = this;

            return new Model('picking.invoice.validation').call('transfer_from_ui',[0,picking_order_id]).then(function(new_picking_ids){
                // if (new_picking_ids) {
                //     // TODO DODAJ CASE
                //     return self.refresh_ui(new_picking_ids[0]);
                // }
                console.log(picking_order_id);

                return 0;
            });



            // return new Model('stock.picking').
            // call('action_done_from_ui',[self.picking.id, self.picking_type_id]).
            // then(function(new_picking_ids){
            //     if (new_picking_ids) {
            //         // TODO DODAJ CASE
            //         return self.refresh_ui(new_picking_ids[0]);
            //     }
            //     return 0;
            // });
        },
        menu: function(){
            $.bbq.pushState('#action=stock_invoice.menu');
            $(window).trigger('hashchange');
        },


        renderElement: function(){
            this._super();
            var self = this;

             this.$('.js_go_to_pick_checking').click(function(){
                var picking_checking_id = $(this).parents("[data-checking-id]:first").data().checkingId;
                self.goto_pickings_checking_by_partner(picking_checking_id);
            });

            this.$('.js_pick_quit').click(function(){
                self.quit();
            });

            this.$('.js_pick_scan').click(function(){
                self.scan_picking($(this).data('id'));
            });
            this.$('.js_pick_last').click(function(){
                self.goto_last_picking_of_type($(this).data('id'));
            });
            this.$('.oe_searchbox').keyup(function(event){
                self.on_searchbox($(this).val());
            });
            this.$('.js_pick_menu').click(function(){
                self.menu();
            });
            //remove navigation bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        barcode_on: function(){
            if (this.is_barcode_on) {
                return;
            }
            this.is_barcode_on = true;
            core.bus.on('barcode_scanned', this, this._barcode_handler);
        },
        barcode_off: function(){
            this.is_barcode_on = false;
            core.bus.off('barcode_scanned', this, this._barcode_handler);
        },
        _barcode_handler: function(barcode){
            this.on_scan(barcode);
        },
        start: function(){
            this._super();
            var self = this;
            //web_client.set_content_full_screen(true);
            self.barcode_on();
            this.loaded.then(function(){
                self.renderElement();
            });
        },
        goto_pickings_checking_by_partner: function(picking_checking_id){
            console.log(picking_checking_id);
            
            $.bbq.pushState('#action=picking_checking.checking&picking_checking_id='+picking_checking_id.toString());
            $(window).trigger('hashchange');

        },
        goto_picking: function(picking_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_id='+picking_id);
            $(window).trigger('hashchange');
        },

        goto_last_picking_of_type: function(type_id){
            $.bbq.pushState('#action=stock_invoice.menu&picking_type_id='+type_id);
            $(window).trigger('hashchange');
        },
        search_picking: function(barcode){
            try {
                var re = new RegExp("([0-9]+):.*?"+barcode.toUpperCase(),"gi");
            } catch(e) {
                //avoid crash if a not supported char is given (like '\' or ')')
                return [];
            }

            var results = [];
            for(var i = 0; i < 100; i++){
                var r = re.exec(this.picking_search_string);
                if(r){
                    var picking = this.pickings_by_id[Number(r[1])];
                    if(picking){
                        results.push(picking);
                    }
                }else{
                    break;
                }
            }
            return results;
        },
        on_scan: function(barcode){
            //OB SKENIRANJU POJDI NA PRAVI INVOICE
            var self = this;
            //barcode = 684;


            if (self.picking_cases.hasOwnProperty(barcode)){
                this.goto_pickings_by_case(barcode);
            }
            this.$('.js_picking_not_found').removeClass('hidden');
            //TODO dodaj opozorilo ce ni pravi picking
            clearTimeout(this.picking_not_found_timeout);
            this.picking_not_found_timeout = setTimeout(function(){
                self.$('.js_picking_not_found').addClass('hidden');
            },2000);

        },
        on_searchbox: function(query){
            var self = this;

            clearTimeout(this.searchbox_timeout);
            this.searchbox_timout = setTimeout(function(){
                if(query){
                    self.$('.js_picking_not_found').addClass('hidden');
                    self.$('.js_picking_categories').addClass('hidden');
                    self.$('.js_picking_search_results').html(
                        qweb.render('PartnerSearchResults',{results:self.search_picking(query)})
                    );
                    self.$('.js_picking_search_results .oe_picking').click(function(){
                        self.goto_pickings_checking_by_partner($(this).data('id') );
                    });
                    self.$('.js_picking_search_results').removeClass('hidden');
                }else{
                    self.$('.js_title_label').removeClass('hidden');
                    self.$('.js_picking_categories').removeClass('hidden');
                    self.$('.js_picking_search_results').addClass('hidden');
                }
            },100);
        },
        quit: function(){
            return new Model("ir.model.data").call("search_read", [[['name', '=', 'stock_picking_type_action']], ['res_id']]).then(function(res) {
                window.location = '/web#action=' + res[0].res_id;
            });
        },
        destroy: function(){
            this._super();
            this.barcode_off();
            //web_client.set_content_full_screen(false);
        }
    });
    core.action_registry.add('picking_checking.partner', PickingCheckingPartnerWidget);

    // PickingCheckingWidget
    var PickingCheckingWidget = MobileWidget.extend({
        template: 'PickingCheckingWidget',
        init: function(parent,params){
            this._super(parent,params);
            var self = this;
            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "stock_invoice.menu"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'stock_invoice.menu',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }
                if (states.action === "picking_checking.partner"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'picking_checking.partner',
                        target: 'current'
                    },{
                        clear_breadcrumbs: true
                    });
                }

            });
            var init_hash = $.bbq.getState();

            this.picking_cases = {};
            this.pickings_by_id = {};
            this.picking_search_string = "";
            this.picking_checking_id = init_hash.picking_checking_id
                ? init_hash.picking_checking_id
                : void 0;

            this.picking_checking = [];
            this.picking = null;
            this.pickings = [];
            this.packoplines = null;
            this.selected_operation = { id: null, picking_order_id: null };
            this.packages = null;
            this.locations = [];
            this.uls = [];
            this.last_pick_ean = '';


            if(this.picking_checking_id){
                this.loaded = this.load(this.picking_checking_id);
            }


        },
        get_new_qty: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].qty;
                }


            }
            return null;

        },
        get_new_qty_done: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].qty_done;
                }


            }
            return null;

        },
        get_new_dest_info: function(pack_operation_product_id){
            var self = this;
            for(var i = 0; i < self.picking_invoice_lines.length; i++){
                if(pack_operation_product_id === self.picking_invoice_lines[i].pack_operation_product[0]){
                    return self.picking_invoice_lines[i].dest_info_text;
                }


            }
            return null;

        },
        get_picking_cases: function(){
            var model = this.getParent();
            var locations = [];
            var self = this;
            var model = this.getParent();
            var pickings = {};
            pickings = model.__parentedChildren[1].picking_cases;


            return pickings;
        },


        // load the picking data from the server. If picking_id is undefined, it will take the first picking
        // belonging to the category
        load: function(picking_checking_id){
            var self = this;

            var model = this.getParent();

            function load_picking_list(picking_checking_id){
                var pickings = new $.Deferred();
                new Model('stock.picking.checking.line').call('search_read',[[['spc_line_id','=',parseInt(picking_checking_id)]]])
                .then(function(picking_checking_lines){
                    if(!picking_checking_lines || picking_checking_lines.length === 0){
                        (new Dialog(self,{
                            title: _t('No Picking Checking Available'),
                            buttons: [{
                                text:_t('Ok'),
                                click: function(){
                                    self.menu();
                                }
                            }]
                        }, _t('<p>We could not find a picking to display.</p>'))).open();

                        pickings.reject();
                    }else{
                        self.pickings = picking_checking_lines;
                        self.packoplines = picking_checking_lines;
                        pickings.resolve(picking_checking_lines);
                    }
                });

                return pickings;
            }

            // if we have a specified picking id, we load that one, and we load the picking of the same type as the active list
            if(picking_checking_id){

                var loaded_picking = new Model('stock.picking.checking').call('search_read',[[['id','=',picking_checking_id]]]).
                then(function(picking_checking){
                    self.picking_checking = picking_checking[0];
                    return load_picking_list(self.picking_checking_id);
                });




            }

            return loaded_picking.then(function(test) {
               console.log("test");
            });

        },
        barcode_on: function(){
            if (this.is_barcode_on) {
                return;
            }
            this.is_barcode_on = true;
            core.bus.on('barcode_scanned', this, this._barcode_handler);
        },
        barcode_off: function(){
            this.is_barcode_on = false;
            core.bus.off('barcode_scanned', this, this._barcode_handler);
        },
        _barcode_handler: function(barcode){
            this.scan(barcode,'None');
        },
        start: function(){
            this._super();
            var self = this;
            //web_client.set_content_full_screen(true);
            self.barcode_on();
            this.$('.js_pick_quit').click(function () {
                self.quit();
            });
            this.$('.js_pick_prev').click(function(){
                self.picking_prev();
            });
            this.$('.js_pick_next').click(function(){
                self.picking_next();
            });
            this.$('.js_pick_menu').click(function(){
                self.menu();
            });
            //TODO Izbor Paketov
            this.$('.js_pick_case').click(function(){
                self.case_pick();
            });

            this.$('.js_reload_op').click(function(){
                self.reload_pack_operation();
            });



            $.when(this.loaded).done(function(){
                self.picking_editor = new PickingCheckingEditorWidget(self);
                self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));

                // if( self.picking.id === self.pickings[0]){
                //     self.$('.js_pick_prev').addClass('disabled');
                // }else{
                //     self.$('.js_pick_prev').removeClass('disabled');
                // }
                //
                // if( self.picking.id === self.pickings[self.pickings.length-1] ){
                //     self.$('.js_pick_next').addClass('disabled');
                // }else{
                //     self.$('.js_pick_next').removeClass('disabled');
                // }
                // if (self.picking.recompute_pack_op){
                //     self.$('.oe_reload_op').removeClass('hidden');
                // }else {
                //     self.$('.oe_reload_op').addClass('hidden');
                // }
                // TODO Gregor
                // self.$('.oe_reload_op').addClass('hidden');
                // if (!self.show_pack){
                //     self.$('.js_pick_pack').addClass('hidden');
                // }
                // if (!self.show_lot){
                //     self.$('.js_create_lot').addClass('hidden');
                // }

            }).fail(function(error) {
                console.log(error);
            });

        },
        on_searchbox: function(query){
            var self = this;
            // self.picking_editor.on_searchbox(query.toUpperCase());
            self.picking_editor.on_searchbox(query);
        },
        // reloads the data from the provided picking and refresh the ui.
        // (if no picking_id is provided, gets the first picking in the db)
        refresh_ui: function(picking_checking_id){
            var self = this;
            var remove_search_filter = "";
            if (parseInt(self.picking_checking_id) === parseInt(picking_checking_id)){
                remove_search_filter = self.$('.oe_searchbox').val();
            }
            return this.load(picking_checking_id).
            then(function(){
                self.picking_editor.remove_blink();
                self.picking_editor.renderElement();
                // if (!self.show_pack){
                //     self.$('.js_pick_pack').addClass('hidden');
                // }
                // if (!self.show_lot){
                //     self.$('.js_create_lot').addClass('hidden');
                // }
                // if (self.picking.recompute_pack_op){
                //     self.$('.oe_reload_op').removeClass('hidden');
                // }else {
                //     self.$('.oe_reload_op').addClass('hidden');
                // }
                //GV
                // if( self.picking.id === self.pickings[0]){
                //     self.$('.js_pick_prev').addClass('disabled');
                // }else{
                //     self.$('.js_pick_prev').removeClass('disabled');
                // }
                //
                // if( self.picking.id === self.pickings[self.pickings.length-1] ){
                //     self.$('.js_pick_next').addClass('disabled');
                // }else{
                //     self.$('.js_pick_next').removeClass('disabled');
                // }
                if (remove_search_filter === ""){
                    self.$('.oe_searchbox').val('');
                    self.on_searchbox('');
                }else{
                    self.$('.oe_searchbox').val(remove_search_filter);
                    self.on_searchbox(remove_search_filter);
                }
            });
        },
        get_header: function(){
            result = '';
            if(this.picking_checking){

                var result = "Partner: "+this.picking_checking.partner_id[1];
                return result;
            }
            return result;
        },
        menu: function(){
            $.bbq.pushState('#action=picking_checking.partner');
            $(window).trigger('hashchange');
        },
        case_pick: function(){

            $.bbq.pushState('#action=picking_case.case&picking_order_id='+this.picking_order_id);

            $(window).trigger('hashchange');
        },
        scan: function(ean, quantity){
            var self = this;

            if (quantity == 'None'){
                quantity = 'None';
            }
            else{
                quantity = parseInt(quantity)
            }


            if (ean.length == 12){
                this.last_pick_ean = ean;
            }
            if (ean.length == 4){
                quantity = parseInt(ean);
                ean = this.last_pick_ean;

            }
            // ean = '5SL116562000';
            var product_visible_ids = this.picking_editor.get_visible_ids();
            return new Model('stock.picking.checking.line').
            call('process_product_id_from_ui', [false,parseInt(self.picking_checking_id),false,ean,true,quantity]).
            then(function(dest_info){

                function sleep (ms) {
                    setTimeout(ms);
                }
                //TODO izpis trenutnega pickinga
                if (dest_info === false){

                    self.$('.js_picking_not_found').removeClass('hidden');


                    //TODO dodaj opozorilo ce ni pravi picking
                    clearTimeout(this.picking_not_found_timeout);
                    this.picking_not_found_timeout = setTimeout(function(){
                        self.$('.js_picking_not_found').addClass('hidden');
                     },5000);

                }

                if (dest_info != ""){
                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').html(dest_info);
                    self.$('.oe_pick_dest_info').removeClass('hidden');

                }


                else{


                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').addClass('hidden');
                }


                setTimeout(function(){
                    self.refresh_ui(parseInt(self.picking_checking_id));
                },5000);

            });
        },
        scan_product_id: function(product_id,line_id,increment,quantity) {
            var self = this;

            if (line_id == false){
                line_id = 0
            }





            //TODO popravi da ne bo fix na [0]
            return new Model('stock.picking.checking.line').
            call('process_product_id_from_ui', [line_id,parseInt(self.picking_checking_id),product_id,false,increment,quantity]).
            then(function(dest_info){
                // TODO iskanje pravega dest_info

                if (dest_info != "" || dest_info != ' <br/>'){
                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').html(dest_info);
                    self.$('.oe_pick_dest_info').removeClass('hidden');

                }


                else{


                    self.$('.oe_pick_last_dest_info').html($('.oe_pick_dest_info').html());
                    self.$('.oe_pick_dest_info').addClass('hidden');
                }

                return self.refresh_ui(parseInt(self.picking_checking_id));
                //return self.refresh_ui(self.picking.id);
            });


        },
        pack: function(){
            var self = this;
            var pack_op_ids = self.picking_editor.get_current_op_selection(false);
            if (pack_op_ids.length !== 0){
                return new Model('stock.picking').
                call('put_in_pack', [[self.picking.id]]).
                then(function(pack){
                    //TODO: the functionality using current_package_id in context is not needed anymore
                    session.user_context.current_package_id = false;
                    // TODO DODAJ CASE
                    return self.refresh_ui(self.picking.id);
                });
            }
        },
        case_done: function(){
            var self = this;
            if (self.case_number){
                self.picking_cases[self.case_number].state = 'done';
            }



            // var pack_op_ids = self.picking_editor.get_current_op_selection(false);
            // if (pack_op_ids.length !== 0){
            //     return new Model('stock.picking').
            //     call('put_in_pack', [[self.picking.id]]).
            //     then(function(pack){
            //         //TODO: the functionality using current_package_id in context is not needed anymore
            //         session.user_context.current_package_id = false;
            //         // TODO DODAJ CASE
            //         return self.refresh_ui(self.picking.id);
            //     });
            // }
            //return self.refresh_ui(self.picking.id);
            return self.refresh_ui(parseInt(self.picking_order_id),parseInt(self.case_number));
        },
        pick_all: function(){
            var self = this;

            for(var i = 0; i < this.packoplines.length; i++){
                self.scan_product_id(this.packoplines[i].product_id[0],this.packoplines[i].id,false,this.packoplines[i].product_qty);

            }



            //
            return self.refresh_ui(parseInt(self.picking_checking_id));
        },
        drop_down: function(){
            var self = this;
            var pack_op_ids = self.picking_editor.get_current_op_selection(true);
            if (pack_op_ids.length !== 0){
                var backorder_model = new Model('stock.backorder.confirmation');
                return backorder_model.call('create', [{'pick_id': self.picking.id}]).then(function(id){
                    return backorder_model.call('process', [id]).then(function(){
                        // TODO DODAJ CASE
                        return self.refresh_ui(self.picking.id).then(function(){
                            if (self.picking_editor.check_done()){
                                return self.done();
                            }
                        });
                    });
                });
            }
        },
        done: function(){
            var self = this;
            return new Model('stock.picking').
            call('action_done_from_ui',[self.picking.id, self.picking_type_id]).
            then(function(new_picking_ids){
                if (new_picking_ids) {
                    // TODO DODAJ CASE
                    return self.refresh_ui(new_picking_ids[0]);
                }
                return 0;
            });
        },
        create_lot: function(op_id, lot_name){
            var self = this;
            return new Model('stock.pack.operation').
            call('create_and_assign_lot',[parseInt(op_id), lot_name]).
            then(function(){
                // TODO DODAJ CASE
                return self.refresh_ui(self.picking.id);
            });
        },
        change_location: function(op_id, loc_id, is_src_dst){
            var self = this;
            var vals = {'location_dest_id': loc_id};
            if (is_src_dst){
                vals = {'location_id': loc_id};
            }
            return new Model('stock.pack.operation').
            call('write',[op_id, vals]).
            then(function(){
                // TODO DODAJ CASE
                return self.refresh_ui(self.picking.id);
            });
        },
        print_package: function(package_id){
            var self = this;
            return new Model('stock.quant.package').
            call('action_print',[[package_id]]).
            then(function(action){
                return self.do_action(action);
            });
        },
        print_picking: function(){
            var self = this;
            return new Model('stock.picking.type').call('read', [[self.picking_type_id], ['code']], {context:new data.CompoundContext()}).
            then(function(pick_type){
                return new Model('stock.picking').call('do_print_picking',[[self.picking.id]]).
                then(function(action){
                    return self.do_action(action);
                });
            });
        },
        picking_next: function(){
            for(var i = 0; i < this.pickings.length; i++){
                if (parseInt(this.pickings[i]) === parseInt(this.case_number)){
                    if(i+1 >= this.pickings.length){
                        this.case_number = parseInt(this.pickings[0]);
                        this.refresh_ui(parseInt(this.picking_order_id),parseInt(this.pickings[0]));
                        break;
                    }
                    else{
                        this.case_number = parseInt(this.pickings[i+1]);
                        this.refresh_ui(parseInt(this.picking_order_id), parseInt(this.pickings[i+1]));
                        break;
                    }
                }
            }
        },
        picking_prev: function(){
            for(var i = 0; i < this.pickings.length; i++){
                if (parseInt(this.pickings[i]) === parseInt(this.case_number)){
                    if(i === 0 ){
                        this.case_number = parseInt(this.pickings[this.pickings.length - 1]);
                        this.refresh_ui(this.picking_order_id,this.pickings[this.pickings.length - 1]);
                        break;
                    }
                    else{
                        this.case_number = parseInt(this.pickings[i-1]);
                        this.refresh_ui(this.picking_order_id, this.pickings[i-1]);
                        break;
                    }
                }
            }
        },
        delete_package_op: function(pack_id){
            var self = this;
            return new Model('stock.pack.operation').call('search', [[['result_package_id', '=', pack_id]]]).
            then(function(op_ids) {
                return new Model('stock.pack.operation').call('write', [op_ids, {'result_package_id':false}]).
                then(function() {
                    // TODO DODAJ CASE
                    return self.refresh_ui(self.picking.id);
                });
            });
        },
        set_operation_quantity: function(product_id,line_id, quantity){
            var self = this;
            if(quantity >= 0){
                // TODO Spremeni funkcijo ...tako k da kliknes na increment


                self.scan_product_id(product_id,line_id,false,quantity);

                // return new Model('stock.pack.operation').
                // call('write',[[op_id],{'qty_done': quantity }]).
                // then(function(){
                //
                //     self.refresh_ui(self.picking.id);
                // });
            }
        },

        set_package_pack: function(package_id, pack){
            var self = this;
            return new Model('stock.quant.package').
            call('write',[[package_id],{'ul_id': pack }]);
        },
        reload_pack_operation: function(){
            var self = this;
            return new Model('stock.picking').
            call('do_prepare_partial',[[self.picking.id]]).
            then(function(){

                // TODO DODAJ CASE
                self.refresh_ui(self.picking.id);
            });
        },
        quit: function(){
            this.destroy();
            return new Model("ir.model.data").call("search_read", [[['name', '=', 'stock_picking_type_action']], ['res_id']]).then(function(res) {
                window.location = '/web#action=' + res[0].res_id;
            });
        },
        destroy: function(){
            this._super();
            //web_client.set_content_full_screen(false);
            this.barcode_off();
        }
    });
    core.action_registry.add('picking_checking.checking', PickingCheckingWidget);



});
