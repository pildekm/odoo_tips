# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class PickingInvoice(models.Model):
	_name = 'picking.invoice'
	_description = 'Picking Invoice'
	_inherit = 'barcodes.barcode_events_mixin'

	#metoda se aktivira po skeniranem izdelku
	def on_barcode_scanned(self, barcode):
		for line in self.order_line:

			if line.product_id.default_code == barcode:
				if line.qty_done + 1 > line.qty:
					return {'warning': {'title': _('Napaka'), 'message': _('Imamo višek izdelkov.')}}
				else:
					line.qty_done += 1
					return {'warning': {'title': _('Uspešno'), 'message': _('Razporejaj  %s') % line.dest_info_line_ids}}




	def process_picking_invoice(self):

		picking_invoice_line_object = self.env['picking.invoice.line']
		purchase_order_line_object = self.env['purchase.order.line']
		if self.state == 'draft':
			for order_line in  self.order_line:
				if order_line.state != 'assigned':
					#TODO -> tle naredi preverjanje, ce ni purchase_order_line_ v primeru da je missing code znan ->
					if order_line.missing_product_id:
						purchase_order_line_id = purchase_order_line_object.search(
							[('product_id', '=', order_line.missing_product_id.id), ('ref_number', '=', order_line.order_number)],
							limit=1)
						if purchase_order_line_id:
							order_line.purchase_order_line_id = purchase_order_line_id
							order_line.missing_product_id = False
					for move_id in order_line.purchase_order_line_id.move_ids:
						if move_id.state == 'assigned':
							for linked_move_operation in move_id.linked_move_operation_ids:
								if linked_move_operation.operation_id != order_line.pack_operation_product:
									order_line.pack_operation_product = linked_move_operation.operation_id.id
							#order_line.pack_operation_product
		return True

	name = fields.Char('Picking Invoice name', required=True)
	invoice_no =  fields.Integer(string="Invoice number", required=True )
	invoice_date = new_field = fields.Date(string="Invoice Date", required=False )
	order_line = fields.One2many('picking.invoice.line', 'picking_order_id', string='Invoice Picking Line')
	state = fields.Selection([
		('draft', 'Draft'), ('cancel', 'Cancelled'),
		('waiting', 'Waiting Another Operation'),
		('confirmed', 'Waiting Availability'),
		('partially_available', 'Partially Available'),
		('assigned', 'Available'), ('done', 'Done')], string='Status', default='draft',
		copy=False, index=True, readonly=True,   track_visibility='onchange',
		help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
		     " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n"
		     " * Waiting Availability: still waiting for the availability of products\n"
		     " * Partially Available: some products are available and reserved\n"
		     " * Ready to Transfer: products reserved, simply waiting for confirmation.\n"
		     " * Transferred: has been processed, can't be modified or cancelled anymore\n"
		     " * Cancelled: has been cancelled, can't be confirmed anymore")

	@api.depends('order_line','order_line.state','order_line.is_done','order_line.qty_done')
	@api.one
	def _compute_state(self):
		''' State of a picking depends on the state of its related stock.move
		 - no moves: draft or assigned (launch_pack_operations)
		 - all moves canceled: cancel
		 - all moves done (including possible canceled): done
		 - All at once picking: least of confirmed / waiting / assigned
		 - Partial picking
		  - all moves assigned: assigned
		  - one of the move is assigned or partially available: partially available
		  - otherwise in waiting or confirmed state
		'''
		state_done = True

		for picking_invoice_line in self.order_line:
			if not(picking_invoice_line.state == 'done' and picking_invoice_line.is_done and picking_invoice_line.qty_done > 0):

				state_done = False

		if state_done:
			self.state = 'done'
		else:
			self.state = 'draft'


	@api.multi
	def validate(self):
		for picking_invoice in self:
			view = self.env.ref('picking_invoice.picking_invoice_validation_view')
			wiz = self.env['picking.invoice.validation'].create({'picking_invoice_id': picking_invoice.id})
			return {
				'name': _('Checking validation?'),
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'picking.invoice.validation',
				'views': [(view.id, 'form')],
				'view_id': view.id,
				'res_id': wiz.id,
				'target': 'new',
				'context': self.env.context,
			}


class PickingInvoiceLine(models.Model):
	_name = 'picking.invoice.line'
	_description = 'Picking Invoice Line'

	#TODO: Gregor def cerate 695 v sale.py
	picking_order_id = fields.Many2one('picking.invoice', string='Picking Order Reference',
	                                   ondelete='cascade', index=True, copy=False)
	stock_move_id = fields.Many2one('stock.move', string='Stock move')
	purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')

	item_shipped = fields.Many2one('product.product', string='Related product send')
	price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
	order_number = fields.Integer(string="Order number", required=True)
	case_number = fields.Integer(string="Case number", required=True)
	qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)

	#qty_done = fields.Float('Done', default=0.0, digits=dp.get_precision('Product Unit of Measure'),related='pack_operation_product.qty_done')
	qty_done = fields.Float('Done', default=0.0, digits=dp.get_precision('Product Unit of Measure'))
	last_qty_done = fields.Float('Last QTY Done', default=0.0, digits=dp.get_precision('Product Unit of Measure'))
	#RELATED FIELDS pack_operation_product


	pack_operation_product = fields.Many2one('stock.pack.operation', string='Stock pack operation', )
	ordered_qty = fields.Float('Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'),
	                           related="pack_operation_product.ordered_qty")
	product_id = fields.Many2one('product.product', 'Product', ondelete="cascade",related="pack_operation_product.product_id")
	product_uom = fields.Many2one('product.uom', 'Unit of Measure',related="pack_operation_product.product_uom_id")
	product_tmpl_id = fields.Many2one(
		'product.template', 'Product Template',
		related='product_id.product_tmpl_id',
		help="Technical: used in views")
	package_id = fields.Many2one('stock.quant.package', 'Source Package', related="pack_operation_product.package_id")
	pack_lot_ids = fields.One2many('stock.pack.operation.lot', 'operation_id', 'Lots/Serial Numbers Used',
	                               related="pack_operation_product.pack_lot_ids")
	result_package_id = fields.Many2one(
		'stock.quant.package', 'Destination Package',
		ondelete='cascade', required=False,
		help="If set, the operations are packed into this package", related="pack_operation_product.result_package_id")
	is_done = fields.Boolean(compute='_compute_is_done', string='Done', readonly=False, oldname='processed_boolean')
	date = fields.Datetime(
		'Date', default=fields.Datetime.now, index=True, required=True,
		states={'done': [('readonly', True)]},
		help="Move date: scheduled date until move is done, then date of actual move processing",related="pack_operation_product.date")

	owner_id = fields.Many2one('res.partner', 'Owner', help="Owner of the quants",related="pack_operation_product.owner_id")
	linked_move_operation_ids = fields.One2many(
		'stock.move.operation.link', 'operation_id', string='Linked Moves',
		readonly=True,
		help='Moves impacted by this operation for the computation of the remaining quantities',related="pack_operation_product.linked_move_operation_ids")
	remaining_qty = fields.Float(string="Remaining Qty", digits=0,
		help="Remaining quantity in default UoM according to moves matched with this operation.",related="pack_operation_product.remaining_qty")
	location_id = fields.Many2one(
		'stock.location', 'Source Location',
		auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
		help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.",related="pack_operation_product.location_id")
	location_dest_id = fields.Many2one(
		'stock.location', 'Destination Location',
		auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
		help="Location where the system will stock the finished products.",related="pack_operation_product.location_dest_id")

	picking_source_location_id = fields.Many2one('stock.location', related="pack_operation_product.picking_source_location_id")
	picking_destination_location_id = fields.Many2one('stock.location', related="pack_operation_product.picking_destination_location_id")
	lots_visible = fields.Boolean(related="pack_operation_product.lots_visible")
	fresh_record = fields.Boolean('Newly created pack operation', related="pack_operation_product.fresh_record",
	                              default=True)
	from_loc = fields.Char(compute='_compute_location_description', related="pack_operation_product.from_loc",
	                       string='From')
	to_loc = fields.Char(compute='_compute_location_description', related="pack_operation_product.to_loc", string='To')
	dest_info_text = fields.Text(string='Dest info', compute='_compute_line_dest_info_text')
	# TDE FIXME: unnecessary fields IMO, to remove

	dest_info_line_ids = fields.One2many('picking.invoice.line.dest_info',  string='Invoice Line Dest Info',compute='_compute_line_dest_info')

	state = fields.Selection(selection=[
		('draft', 'Draft'),
		('cancel', 'Cancelled'),
		('waiting', 'Waiting Another Operation'),
		('confirmed', 'Waiting Availability'),
		('partially_available', 'Partially Available'),
		('assigned', 'Available'),
		('done', 'Done')], related='pack_operation_product.state')
	missing_product_id  = fields.Many2one('product.product', 'Missing Product', ondelete="cascade",)
	#TODO TLE pojdi po pack_operation_product... dodajaj + 1

	@api.depends('qty_done')
	@api.onchange('qty_done')
	def change_qty_done(self,new_qty=None):

		print self[0]
		invoice_order = self[0].picking_order_id
		picking_invoice_line_ids = self.search(
			[('picking_order_id', '=', invoice_order.id), ('state', '=', 'available')])
		if new_qty != None:
			invoice_order_line = self
		else:
			invoice_order_line = self._origin
		picking_invoice_line_ids = invoice_order_line.picking_order_id.order_line

		#new_qty_done = invoice_order_line.qty_done
		new_qty_done = 0
		if new_qty != None:
			invoice_order_line.write({'qty_done': new_qty})
		else:
			invoice_order_line.write({'qty_done': self.qty_done})
		#invoice_order_line.qty_done = self.qty_done
		for invoice_order_line_item in picking_invoice_line_ids:
			if invoice_order_line_item.product_id == invoice_order_line.product_id and not invoice_order_line == invoice_order_line_item:
				new_qty_done += invoice_order_line_item.qty_done
		if new_qty != None:
			new_qty_done += new_qty
		else:
			new_qty_done += self.qty_done

		invoice_order_line.pack_operation_product.write({'qty_done': new_qty_done})


		#for item in self:


		# picking_invoice_line_object = self.env['picking.invoice.line']
		# purchase_order_line_id = self._origin.purchase_order_line_id
		# picking_invoice_line_ids = picking_invoice_line_object.search([('purchase_order_line_id','=',purchase_order_line_id.id),('state','=','available')])
		#
		# current_qty_done = 0.0
		# for picking_invoice_line in picking_invoice_line_ids:
		# 	current_qty_done += picking_invoice_line.qty_done
		#
		# real_current_pack_operation_qty_done = current_qty_done - self._origin.qty_done
		# set_current_pack_operation_qty_done = real_current_pack_operation_qty_done + self.qty_done
		#
		#
		# self.pack_operation_product.write({'qty_done': set_current_pack_operation_qty_done})
		# self._origin.write({'qty_done':self.qty_done})

		#set_current_pack_operation_qty_done = self.qty_done
		#self.pack_operation_product.write({'qty_done': set_current_pack_operation_qty_done})
		# # self._origin.write({'qty_done': set_current_pack_operation_qty_done})






	@api.one
	def _compute_is_done(self):
		self.is_done = self.qty_done > 0.0


	@api.onchange('is_done')
	def on_change_is_done(self):
		if not self.product_id:
			if self.is_done and self.qty_done == 0:
				self.qty_done = 1.0
			if not self.is_done and self.qty_done != 0:
				self.qty_done = 0.0




	@api.onchange('pack_operation_product')
	@api.multi
	def _compute_line_dest_info(self):

		for picking_invoice_line in self:
			dest_info_values = {}
			dest_info_values2 = {}
			search_domain = []
			search_domain.append(('purchase_order_line_id', '=', picking_invoice_line.purchase_order_line_id.id))

			if picking_invoice_line.picking_order_id.state == 'done':
				search_domain.append(('state', '=', 'done'))
			else:
				search_domain.append(('state', '!=', 'done'))

			for move_operation in picking_invoice_line.linked_move_operation_ids:
				if not move_operation.move_id.id in dest_info_values:
					dest_info_values[move_operation.move_id.id] = {}
				dest_info_values[move_operation.move_id.id]['qty'] = move_operation.qty
				dest_info_values[move_operation.move_id.id]['move_id'] = move_operation.move_id
				dest_info_values[move_operation.move_id.id]['remaining_qty'] = move_operation.qty
				dest_info_values[move_operation.move_id.id]['picking_invoice_line'] = picking_invoice_line
				dest_info_values[move_operation.move_id.id]['dest_info_values'] = []

			# for move_id in picking_invoice_line.purchase_order_line_id.move_ids:
			# 	if not move_id.id in dest_info_values:
			# 		dest_info_values[move_id.id] = {}
			# 	dest_info_values[move_id.id]['qty'] = move_id.product_qty
			# 	dest_info_values[move_id.id]['move_id'] = move_id.id
			# 	dest_info_values[move_id.id]['remaining_qty'] = move_id.product_qty
			# 	dest_info_values[move_id.id]['picking_invoice_line'] = picking_invoice_line
			# 	dest_info_values[move_id.id]['dest_info_values'] = []

			invoice_line_ids_purchase_line_same = self.env['picking.invoice.line'].search(search_domain)
			qty_ordered = []
			for purchase_line_same in invoice_line_ids_purchase_line_same:
				data_values = {
					'invoice_picking_id': purchase_line_same.id,
					'qty': purchase_line_same.qty,
					'remaining_qty': purchase_line_same.qty,
					'dest_info_values': []
				}
				qty_ordered.append(data_values)
			for j, invoice_picking_id in enumerate(qty_ordered):
				for i, move_id in enumerate(dest_info_values):

					# if dest_info_values[move_id]['remaining_qty']:

					if picking_invoice_line.picking_order_id.state == 'done':
						# TODO Tle je napaka, ko je invoice.picking že opravljen
						if qty_ordered[j]['remaining_qty'] and dest_info_values[move_id]['qty']:
							if qty_ordered[j]['remaining_qty'] >= dest_info_values[move_id]['qty']:
								new_data_values = {
									'move_id': move_id,
									'qty': dest_info_values[move_id]['qty'],
									# 'invoice_picking_id': invoice_picking_id
								}
								qty_ordered[j]['remaining_qty'] -= new_data_values['qty']
								dest_info_values[move_id]['remaining_qty'] -= new_data_values['qty']

								qty_ordered[j]['dest_info_values'].append(new_data_values)
								dest_info_values[move_id]['dest_info_values'].append(new_data_values)

							else:
								new_data_values = {
									'move_id': move_id,
									'qty': qty_ordered[j]['remaining_qty'],
									# 'invoice_picking_id': invoice_picking_id
								}
								qty_ordered[j]['remaining_qty'] -= new_data_values['qty']
								dest_info_values[move_id]['remaining_qty'] -= new_data_values['qty']

								qty_ordered[j]['dest_info_values'].append(new_data_values)
								dest_info_values[move_id]['dest_info_values'].append(new_data_values)


					else:
						#TODO Tle je napaka, ko je invoice.picking že opravljen
						if qty_ordered[j]['remaining_qty'] and dest_info_values[move_id]['remaining_qty']:
							if qty_ordered[j]['remaining_qty'] >= dest_info_values[move_id]['remaining_qty']:
								new_data_values = {
									'move_id': move_id,
									'qty': dest_info_values[move_id]['remaining_qty'],
									# 'invoice_picking_id': invoice_picking_id
								}
								qty_ordered[j]['remaining_qty'] -= new_data_values['qty']
								dest_info_values[move_id]['remaining_qty'] -= new_data_values['qty']

								qty_ordered[j]['dest_info_values'].append(new_data_values)
								dest_info_values[move_id]['dest_info_values'].append(new_data_values)

							else:
								new_data_values = {
									'move_id': move_id,
									'qty': qty_ordered[j]['remaining_qty'],
									# 'invoice_picking_id': invoice_picking_id
								}
								qty_ordered[j]['remaining_qty'] -= new_data_values['qty']
								dest_info_values[move_id]['remaining_qty'] -= new_data_values['qty']

								qty_ordered[j]['dest_info_values'].append(new_data_values)
								dest_info_values[move_id]['dest_info_values'].append(new_data_values)

			dest_info_ids = []
			for qty_order_data in qty_ordered:
				new_dest_info = ''
				if qty_order_data['invoice_picking_id'] == picking_invoice_line.id:
					for qty_info_data in qty_order_data['dest_info_values']:
						# invoice_picking_id
						#TODO tle zafilaj dest_info_line_char
						dest_info_id = self.env['picking.invoice.line.dest_info'].create(qty_info_data)
						dest_info_ids.append(dest_info_id.id)
			picking_invoice_line.dest_info_line_ids = dest_info_ids

	@api.multi
	def _compute_line_dest_info_text(self):

		for line in self:
			return_char = ''
			for dest_info in line.dest_info_line_ids:
				if return_char != '':
					return_char += ' <br />'
				if dest_info.picking_partner_id:
					return_char += ' '+dest_info.picking_partner_id.name+ ' | '+str(dest_info.qty)
				else:
					return_char += ' | '+str(dest_info.qty)


			line.dest_info_text = return_char


class PickingInvoiceLineDestInfo(models.TransientModel):
	_name = 'picking.invoice.line.dest_info'
	_description = 'Picking Invoice Line Dest Info'

	#picking_invoice_line_id = fields.Many2one('picking.invoice.line', string='Picking Invoice Line', required=True,ondelete='cascade', index=True, copy=False)
	# picking_invoice_line_id = fields.Many2one('picking.invoice.line', string='Picking Invoice Line')
	move_id = fields.Many2one(
		'stock.move', 'Move',
		ondelete="cascade", required=True)
	qty = fields.Float('Quantity', default=0.0, digits=dp.get_precision('Product Unit of Measure'))
	picking_partner_id = fields.Many2one('res.partner', 'Transfer Destination Address', related='move_id.move_dest_id.picking_partner_id')
	# @api.one
	# @api.depends('picking_invoice_line_id')
	# def _compute_dest_qty(self):
	# 	print "tle sem"


	def get_dest_info(self):
		print "tle sem"
		return_string = ''
		for dest_info_item in self:
			return_string +=  dest_info_item.picking_partner_id.name+' : ' + str(dest_info_item.qty)+' kom'
		return return_string
