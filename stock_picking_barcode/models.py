# -*- coding: utf-8 -*-

from odoo import models, api,fields

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.multi
    def new_sort_and_create(self):

        res = self.get_data()
        data = {}
        vals = {}
        for r in res:
            for o in r.pack_operation_ids:
                if r.partner_id.id in data:
                    data[r.partner_id.id].append({'product_id': o.product_id.id, 'product_qty': o.product_qty,
                                                  'qty_done': o.qty_done, 'name': r.name, 'operation_id': o.id,
                                                  'po_id': o.id,
                                                  'location_dest_id': o.location_dest_id.id,
                                                  'origin': r.origin, 'state': o.state, 'partner_id': r.partner_id.id,
                                                  'picking_id': o.picking_id.id, 'sp_id': o.picking_id.id})
                else:
                    data[r.partner_id.id] = [{'product_id': o.product_id.id, 'product_qty': o.product_qty,
                                              'qty_done': o.qty_done, 'name': r.name, 'operation_id': o.id,
                                              'po_id': o.id,
                                              'location_dest_id': o.location_dest_id.id,
                                              'origin': r.origin, 'state': o.state, 'partner_id': r.partner_id.id,
                                              'picking_id': o.picking_id.id, 'sp_id': o.picking_id.id}]

        SPCL_obj = self.env['stock.picking.checking.line']
        SPC_obj = self.env['stock.picking.checking']
        lines = []
        for d in data:
            lines = [(0, 0, {'product_id': a['product_id'], 'product_qty': a['product_qty'],
                             'qty_done': a['qty_done'], 'name': a['name'],
                             'location_dest_id': a['location_dest_id'],
                             'origin': a['origin'], 'state': a['state'], 'partner_id': a['partner_id'],
                             'picking_id': a['picking_id'], 'sp_id': a['sp_id'], 'operation_id': a['operation_id'],
                             'po_id': a['po_id'], 'spc_line_id': 1}) for a in data[d]]

            vals.update({'partner_id': d, 'spc_line': lines})
            SPC_obj.create(vals)
            vals = {}
            lines = []

        search_view_id = self.env.ref('stock_picking_checking.stock_picking_checking_search', False).id

        return True




class StockPickingChecking(models.Model):
    _inherit = 'stock.picking.checking'

    def validate_all_checkings(self):

        for pick in self:
            wiz = self.env['stock.checking.validation'].transfer(pick.id)

    @api.multi
    def add_product_to_sale_order(self,partner_id,product_id, quantity):
        sale_order_object = self.env['sale.order']
        sale_order_line_object = self.env['sale.order.line']

        sale_order_line_values = {
            'product_uom_qty' : quantity,
            'product_id': product_id

        }
        sale_order = sale_order_object.search([('partner_id','=',partner_id),('state','=','draft')])
        if sale_order:
            sale_order_line_values['order_id'] = sale_order.id
            # new_sale_order_line = self.sale_order_line.copy(default={'order_id': sale_order.id, 'product_uom_qty': self.product_uom_qty})
            new_sale_order_line = sale_order_line_object.create(sale_order_line_values)

            if sale_order.note:
                sale_order.note += ' \nIz checking: izdelek: ' + new_sale_order_line.product_id.name+' '+ new_sale_order_line.product_id.default_code
            else:
                sale_order.note = 'Iz checking: izdelek: ' + new_sale_order_line.product_id.name+' '+ new_sale_order_line.product_id.default_code

        else:
            sale_order_values = {
                'partner_id': partner_id,
            }
            sale_order = sale_order_object.create(sale_order_values)
            #new_sale_order_line = self.sale_order_line.copy(default={'order_id': sale_order.id, 'product_uom_qty': self.product_uom_qty})
            sale_order_line_values['order_id'] = sale_order.id
            new_sale_order_line = sale_order_line_object.create(sale_order_line_values)
            sale_order.note = 'Iz checking: izdelek: ' + new_sale_order_line.product_id.name+' '+ new_sale_order_line.product_id.default_code





class PackOperation(models.Model):
    _inherit = "stock.pack.operation"


    dest_info = fields.Text('Destination info')





class StockPickingCheckingLine(models.Model):
    _inherit =  'stock.picking.checking.line'

    # TODO najdi najprej objekt glede na case, invoice_no, in produkt
    @api.multi
    def process_product_id_from_ui(self, picking_order_id, product_id=False, ean=False, increment=True,
                                   quantity=None):
        if len(self) == 0:
            picking_checking_line = False
        else:
            picking_checking_line = self.search([('id','=',self.id)], limit=1)
        product_product_obj = self.env['product.product']
        if ean:
            product_id = product_product_obj.search([('default_code', '=', ean)], limit=1).id

        if not picking_checking_line and product_id:
            picking_checking_line = self.search(
                [('spc_line_id', '=', picking_order_id),
                 ('product_id', '=', product_id)])
        if not picking_checking_line:
            return False
        if len(picking_checking_line) == 0:
            return False
        if len(picking_checking_line) > 1:
            for line in picking_checking_line:
                if increment == False:
                    if line.qty_done > 0:
                        picking_checking_line = line
                        break
                else:
                    if line.qty_done < line.qty:
                        picking_checking_line = line
                        break
        pack_operation_object = self.env['stock.pack.operation']
        stock_pack_operation = pack_operation_object.search([('id','=',picking_checking_line.po_id)],limit=1)
        if len(stock_pack_operation) == 0:
            return ''



        if quantity == 'None' or quantity == None:
            qty = picking_checking_line.qty_done
            if increment:
                qty += 1
            else:
                if qty >= 1:
                    qty -= 1
                else:
                    qty = 0
        else:
            qty = quantity

        start_qty = picking_checking_line.qty_done
        if start_qty > picking_checking_line.product_qty:
            start_qty = 0
        remain_start_qty = start_qty
        change_qty = qty - start_qty
        picking_checking_line.qty_done = qty
        picking_checking_line.write({'qty_done': qty})
        stock_pack_operation.qty_done = qty
        #picking_checking_line.change_qty_done(qty)
        return_dest_info = ''
        if change_qty > 0:
            return_dest_info += picking_checking_line.product_id.display_name +' | '+ str(change_qty)
        calc_qty = 0

        # if qty > picking_order_line.ordered_qty:
        #     return ''
        #
        # remain_qty = change_qty
        #
        # if remain_qty > 0:
        #     return_dest_info = picking_order_line.product_id.display_name
        #
        # for dest_info in picking_order_line.dest_info_line_ids:
        #     # TODO SESTEJ IN SE ODLOCI ZA KOGA JE TA DEL
        #
        #     if return_dest_info != picking_order_line.product_id.display_name:
        #         return_dest_info += ' <br/>'
        #     if remain_qty > 0:
        #         if remain_start_qty >= dest_info.qty:
        #             remain_start_qty -= dest_info.qty
        #             continue
        #
        #         else:
        #
        #             if (remain_start_qty + remain_qty) >= dest_info.qty:
        #
        #                 return_dest_info += ' | ' + dest_info.picking_partner_id.name + ' | ' + str(
        #                     dest_info.qty - remain_start_qty)
        #                 calc_qty += change_qty
        #                 remain_qty -= dest_info.qty
        #                 remain_qty += remain_start_qty
        #                 remain_start_qty -= remain_start_qty
        #
        #             else:
        #
        #                 return_dest_info += ' | ' + dest_info.picking_partner_id.name + ' | ' + str(remain_qty)
        #                 calc_qty += change_qty
        #                 return return_dest_info

        return return_dest_info

class PickingInvoiceLine(models.Model):
    _inherit = "picking.invoice.line"


    @api.multi
    def process_barcode_from_ui(self, barcode_str, visible_op_ids):
        """This function is called each time there barcode scanner reads an input"""
        self.ensure_one()
        lot_obj = self.env['stock.production.lot']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        pack_op = self.env['stock.pack.operation'].search(
            [('picking_id', '=', self.id)])
        stock_location_obj = self.env['stock.location']
        answer = {'filter_loc': False, 'operation_id': False}
        # check if the barcode correspond to a location
        matching_location_ids = stock_location_obj.search([('barcode', '=', barcode_str)])
        if matching_location_ids:
            # if we have a location, return immediatly with the location name
            location = matching_location_ids.name_get()[0]
            answer['filter_loc'] = location[1]
            answer['filter_loc_id'] = location[0]
        # check if the barcode correspond to a product
        matching_product_ids = product_obj.search(
            ['|', ('barcode', '=', barcode_str), ('default_code', '=', barcode_str)])
        if matching_product_ids:
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', matching_product_ids[0].id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a lot
        matching_lot_ids = lot_obj.search([('name', '=', barcode_str)])
        if matching_lot_ids:
            lot = lot_obj.browse(matching_lot_ids[0].id)
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', lot.product_id.id), ('pack_lot_ids.lot_id', '=', lot.id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a package
        matching_package_ids = package_obj.search([('name', '=', barcode_str)])
        if matching_package_ids:
            op_id = pack_op._increment(
                self.id,
                [('package_id', '=', matching_package_ids[0])],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        return answer



    @api.multi
    def process_barcode_from_ui(self, barcode_str, visible_op_ids):
        """This function is called each time there barcode scanner reads an input"""
        self.ensure_one()
        lot_obj = self.env['stock.production.lot']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        pack_op = self.env['stock.pack.operation'].search(
            [('picking_id', '=', self.id)])
        stock_location_obj = self.env['stock.location']
        answer = {'filter_loc': False, 'operation_id': False}
        # check if the barcode correspond to a location
        matching_location_ids = stock_location_obj.search([('barcode', '=', barcode_str)])
        if matching_location_ids:
            # if we have a location, return immediatly with the location name
            location = matching_location_ids.name_get()[0]
            answer['filter_loc'] = location[1]
            answer['filter_loc_id'] = location[0]
        # check if the barcode correspond to a product
        matching_product_ids = product_obj.search(
            ['|', ('barcode', '=', barcode_str), ('default_code', '=', barcode_str)])
        if matching_product_ids:
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', matching_product_ids[0].id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a lot
        matching_lot_ids = lot_obj.search([('name', '=', barcode_str)])
        if matching_lot_ids:
            lot = lot_obj.browse(matching_lot_ids[0].id)
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', lot.product_id.id), ('pack_lot_ids.lot_id', '=', lot.id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a package
        matching_package_ids = package_obj.search([('name', '=', barcode_str)])
        if matching_package_ids:
            op_id = pack_op._increment(
                self.id,
                [('package_id', '=', matching_package_ids[0])],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        return answer


    @api.model
    def get_invoice_lines_w_dest_info(self, picking_order_id, case_number):
        invoice_lines = self.search([('picking_order_id','=',picking_order_id),('case_number','=',case_number)])
        for invoice_line in invoice_lines:
            print invoice_line

        return invoice_lines



    @api.model
    def get_current_dest_info(self, dest_info_ids):
        dest_info_object = self.env['picking.invoice.line.dest_info']
        dest_infos = dest_info_object.search([('id','in',dest_info_ids)])
        return_dest_info = ''
        for dest_info in dest_infos:
            return_dest_info += dest_info.picking_partner_id.name
        return return_dest_info

    #TODO najdi najprej objekt glede na case, invoice_no, in produkt
    @api.multi
    def process_product_id_from_ui(self,picking_order_id,case_number,product_id= False,ean = False, increment=True,quantity = None):
        picking_order_line = False
        product_product_obj = self.env['product.product']
        if ean:
            product_id = product_product_obj.search([('default_code','=',ean)],limit=1).id

        #TODO VEC ISTIH POSTAVK V PAKETU
        if product_id:
            picking_order_line = self.search([('picking_order_id','=',picking_order_id),('case_number','=',case_number),('product_id','=',product_id)])

        if picking_order_line == False or len(picking_order_line) == 0:
            return False
        if len(picking_order_line) > 1:
            for line in picking_order_line:
                if increment == False:
                    if line.qty_done > 0:
                        picking_order_line = line
                        break
                else:
                    if line.qty_done < line.qty:
                        picking_order_line = line
                        break


        if quantity == 'None' or quantity == None:
            qty = picking_order_line.qty_done
            if increment:
                qty += 1
            else:
                if qty >= 1:
                    qty -= 1
                else:
                    qty = 0
        else:
            qty = quantity

        start_qty = picking_order_line.qty_done
        if start_qty > picking_order_line.ordered_qty:
            start_qty = 0
        remain_start_qty = start_qty
        change_qty = qty - start_qty
        picking_order_line.qty_done = qty
        picking_order_line.write({'qty_done': qty})
        picking_order_line.change_qty_done(qty)
        return_dest_info = ''
        calc_qty = 0

        if qty > picking_order_line.ordered_qty:
            return ''

        remain_qty = change_qty

        if remain_qty > 0 :
            return_dest_info = picking_order_line.product_id.display_name

        for dest_info in picking_order_line.dest_info_line_ids:
            #TODO SESTEJ IN SE ODLOCI ZA KOGA JE TA DEL

            if return_dest_info != picking_order_line.product_id.display_name:
                return_dest_info += ' <br/>'
            if remain_qty > 0:
                if remain_start_qty >= dest_info.qty:
                    remain_start_qty -= dest_info.qty
                    continue

                else:

                    if (remain_start_qty + remain_qty) >= dest_info.qty:

                        return_dest_info += ' | '+ dest_info.picking_partner_id.name + ' | '+str(dest_info.qty-remain_start_qty)
                        calc_qty += change_qty
                        remain_qty -= dest_info.qty
                        remain_qty += remain_start_qty
                        remain_start_qty -= remain_start_qty

                    else:

                        return_dest_info +=  ' | '+  dest_info.picking_partner_id.name + ' | '+ str(remain_qty)
                        calc_qty += change_qty
                        return return_dest_info

        return return_dest_info




    @api.model
    def get_next_picking_for_ui(self, picking_order_id):
        """ returns the next pickings to process. Used in the barcode scanner UI"""
        domain = [('picking_order_id', '=', picking_order_id)]
        cases = []
        pickings = self.search(domain)
        for picking in pickings:
            if picking.case_number not in cases:
                cases.append(picking.case_number)
        cases.sort()
        return cases







class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def process_barcode_from_ui(self, barcode_str, visible_op_ids):
        """This function is called each time there barcode scanner reads an input"""
        self.ensure_one()
        lot_obj = self.env['stock.production.lot']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        pack_op = self.env['stock.pack.operation'].search(
            [('picking_id', '=', self.id)])
        stock_location_obj = self.env['stock.location']
        answer = {'filter_loc': False, 'operation_id': False}
        # check if the barcode correspond to a location
        matching_location_ids = stock_location_obj.search([('barcode', '=', barcode_str)])
        if matching_location_ids:
            # if we have a location, return immediatly with the location name
            location = matching_location_ids.name_get()[0]
            answer['filter_loc'] = location[1]
            answer['filter_loc_id'] = location[0]
        # check if the barcode correspond to a product
        matching_product_ids = product_obj.search(['|', ('barcode', '=', barcode_str), ('default_code', '=', barcode_str)])
        if matching_product_ids:
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', matching_product_ids[0].id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a lot
        matching_lot_ids = lot_obj.search([('name', '=', barcode_str)])
        if matching_lot_ids:
            lot = lot_obj.browse(matching_lot_ids[0].id)
            op_id = pack_op._increment(
                self.id,
                [('product_id', '=', lot.product_id.id), ('pack_lot_ids.lot_id', '=', lot.id)],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        # check if the barcode correspond to a package
        matching_package_ids = package_obj.search([('name', '=', barcode_str)])
        if matching_package_ids:
            op_id = pack_op._increment(
                self.id,
                [('package_id', '=', matching_package_ids[0])],
                filter_visible=True,
                visible_op_ids=visible_op_ids,
                increment=True
            )
            answer['operation_id'] = op_id.id
            return answer
        return answer

    @api.model
    def get_next_picking_for_ui(self, picking_type_id=None):
        """ returns the next pickings to process. Used in the barcode scanner UI"""
        domain = [('state', 'in', ('assigned', 'partially_available'))]
        if picking_type_id:
            domain.append(('picking_type_id', '=', picking_type_id))
        return self.search(domain).ids

    @api.model
    def check_group_lot(self):
        """ This function will return true if we have the setting to use lots activated. """
        return self.env['res.users'].has_group('stock.group_production_lot')

    @api.model
    def check_group_pack(self):
        """ This function will return true if we have the setting to use package activated. """
        return self.env['res.users'].has_group('stock.group_tracking_lot')

    def action_assign_owner(self):
        for picking in self:
            packop_ids = [op.id for op in picking.pack_operation_ids]
            self.env['stock.pack.operation'].write(packop_ids, {'owner_id': picking.owner_id.id})

    @api.multi
    def process_product_id_from_ui(self, product_id, op_id, increment=True):

        self.ensure_one()
        pack_op = self.env['stock.pack.operation'].search(
            [('picking_id', '=', self.id)])
        op_obj = pack_op._increment(
            self.id,
            [('product_id', '=', product_id), ('id', '=', op_id)],
            increment=increment
        )
        return op_obj.id

    @api.model
    def action_pack(self, picking_ids, operation_filter_ids=None):
        """ Create a package with the current pack_operation_ids of the picking that aren't yet in a pack.
        Used in the barcode scanner UI and the normal interface as well.
        operation_filter_ids is used by barcode scanner interface to specify a subset of operation to pack"""
        if operation_filter_ids is None:
            operation_filter_ids = []
        stock_operation_obj = self.env['stock.pack.operation']
        package_obj = self.env['stock.quant.package']
        stock_move_obj = self.env['stock.move']
        package_id = False
        for picking_id in picking_ids:
            operation_search_domain = [('picking_id', '=', picking_id), ('result_package_id', '=', False)]
            if operation_filter_ids != []:
                operation_search_domain.append(('id', 'in', operation_filter_ids))
            operation_ids = stock_operation_obj.search(operation_search_domain)
            pack_operation_ids = []
            if operation_ids:
                for operation in stock_operation_obj.browse(operation_ids):
                    # If we haven't done all qty in operation, we have to split into 2 operation
                    op = operation
                    if (operation.qty_done < operation.product_qty):
                        new_operation = operation.copy(
                            {'product_qty': operation.qty_done, 'qty_done': operation.qty_done},
                        )
                        operation.write(
                            {'product_qty': operation.product_qty - operation.qty_done, 'qty_done': 0},
                        )
                        op = stock_operation_obj.browse(new_operation)
                    pack_operation_ids.append(op.id)
                    if op.product_id and op.location_id and op.location_dest_id:
                        stock_move_obj.check_tracking_product(
                            op.product_id,
                            op.lot_id.id,
                            op.location_id,
                            op.location_dest_id
                        )
                package_id = package_obj.create({})
                stock_operation_obj.browse(pack_operation_ids).write(
                    {'result_package_id': package_id},
                )
        return package_id

    def action_done_from_ui(self, picking_id):
        """ called when button 'done' is pushed in the barcode scanner UI """
        # write qty_done into field product_qty for every package_operation before doing the transfer
        for operation in self.browse(picking_id).pack_operation_ids:
            operation.with_context(no_recompute=True).write({'product_qty': operation.qty_done})
        self.do_transfer()
        # return id of next picking to work on
        return self.get_next_picking_for_ui()

    def unpack(self):
        quant_obj = self.env['stock.quant']
        for package in self:
            quant_ids = [quant.id for quant in package.quant_ids]
            quant_obj.write(quant_ids, {'package_id': package.parent_id.id or False})
            children_package_ids = [child_package.id for child_package in package.children_ids]
            self.write(children_package_ids, {'parent_id': package.parent_id.id or False})
        # delete current package since it contains nothing anymore
        self.unlink()
        return self.env['ir.actions.act_window'].for_xml_id(
            'stock',
            'action_package_view',
        )

    @api.multi
    def open_barcode_interface(self):
        picking_ids = self.ids
        final_url = "/barcode/web/?debug=assets#action=stock_invoice.menu"
        return {'type': 'ir.actions.act_url', 'url': final_url, 'target': 'self', }

    @api.model
    def do_partial_open_barcode(self, picking_ids):
        self.do_prepare_partial(picking_ids)
        return self.open_barcode_interface(picking_ids)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def open_barcode_interface(self):
        final_url = ''
        if self.id == 1:
            final_url = "/barcode/web/?debug=assets#action=stock_invoice.menu"

        else:
            final_url = "/barcode/web/?debug=assets#action=picking_checking.partner"

        return {'type': 'ir.actions.act_url', 'url': final_url, 'target': 'self'}



class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def _increment(self, picking_id, domain, filter_visible=False, visible_op_ids=False, increment=True):
        """Search for an operation with given 'domain' in a picking, if it exists increment the qty (+1) otherwise create it

        :param domain: list of tuple directly reusable as a domain
        context can receive a key 'current_package_id' with the package to consider for this operation
        returns True
        """
        # if current_package_id is given in the context, we increase the number of items in this package
        package_clause = [('result_package_id', '=', self.env.context.get('current_package_id', False))]
        existing_operation_ids = self.search([('picking_id', '=', picking_id)] + domain + package_clause)
        todo_operation_ids = []
        if existing_operation_ids:
            if filter_visible:
                todo_operation_ids = [val for val in existing_operation_ids if val.id in visible_op_ids]
            else:
                todo_operation_ids = existing_operation_ids
        if todo_operation_ids:
            # existing operation found for the given domain and picking => increment its quantity
            op_obj = todo_operation_ids[0]
            # when op_object has a lot
            qty = op_obj.qty_done
            if increment:
                qty += 1
            else:
                qty -= 1 if qty >= 1 else 0
                if qty == 0 and op_obj.product_qty == 0:
                    # we have a line with 0 qty set, so delete it
                    self.unlink()
                    return op_obj
            op_obj.write({'qty_done': qty})
        else:
            # no existing operation found for the given domain and picking => create a new one
            picking_obj = self.env["stock.picking"]
            picking = picking_obj.browse(picking_id)
            values = {
                'picking_id': picking_id,
                'product_qty': 0,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'qty_done': 1,
            }
            for key in domain:
                var_name, dummy, value = key
                uom_id = False
                if var_name == 'product_id':
                    uom_id = self.env['product.product'].browse(value).uom_id.id
                if var_name == 'pack_lot_ids.lot_id':
                    update_dict = {'pack_lot_ids': [(0, 0, {'lot_id': value})]}
                else:
                    update_dict = {var_name: value}
                if uom_id:
                    update_dict['product_uom_id'] = uom_id
                values.update(update_dict)
            op_obj = self.create(values)
        return op_obj

    @api.multi
    def create_and_assign_lot(self, name):
        """ Used by barcode interface to create a new lot and assign it to the operation """
        self.ensure_one()
        product_id = self.product_id.id
        val = {'product_id': product_id}
        new_lot_id = False
        if name:
            lots = self.env['stock.production.lot'].search(
                ['&', ('name', '=', name), ('product_id', '=', product_id)],
            )
            if lots:
                new_lot_id = lots.ids[0]
            val.update({'name': name})

        if not new_lot_id:
            new_lot_id = self.env['stock.production.lot'].create(val).id
        self.write({'pack_lot_ids': [(0, 0, {'lot_id': new_lot_id})]})
