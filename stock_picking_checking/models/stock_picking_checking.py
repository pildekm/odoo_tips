# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class StockPickingChecking(models.Model):
	_name = 'stock.picking.checking'
	_inherit = 'barcodes.barcode_events_mixin'


	@api.multi
	def write(self, vals):
		res = super(StockPickingChecking, self).write(vals)
		for v in vals:
			for val in vals[v]:
				index = self.spc_line.ids.index(val[1])
				if val[2]:
					if val[2]['qty_done'] > self.spc_line[index].product_qty:
						visek = val[2]['qty_done'] - self.spc_line[index].product_qty
						raise UserError(_('Imamo višek izdelkov. [%s x %s]') %(visek, self.spc_line[index].product_id.name))
		return res

	#metoda se aktivira po skeniranem izdelku
	def on_barcode_scanned(self, barcode):
		for line in self.spc_line:
			if line.product_id.code == barcode:
				if line.qty_done > line.product_qty:
					return {'warning': {'title': _('Napaka'), 'message': _('Imamo višek izdelkov.')}}
				else:
					line.qty_done += 1
			# else:
			# 	return {'warning': {'title': _('Napaka'), 'message': _('Skenirani izdelek ni na listi.')}}

	@api.multi
	def validate(self):
		for pick in self:
			view = self.env.ref('stock_picking_checking.stock_checking_validation_view')
			wiz = self.env['stock.checking.validation'].create({'pick_id': pick.id})
			return {
	                    'name': _('Checking validation?'),
	                    'type': 'ir.actions.act_window',
	                    'view_type': 'form',
	                    'view_mode': 'form',
	                    'res_model': 'stock.checking.validation',
	                    'views': [(view.id, 'form')],
	                    'view_id': view.id,
						'res_id': wiz.id,
	                    'target': 'new',
	                    'context': self.env.context,
	                }

	@api.multi
	def validate_all(self):
		for pick in self:
			view = self.env.ref('stock_picking_checking.stock_checking_transfer_all_view')
			wiz = self.env['stock.checking.transfer.all'].create({'pick_id': pick.id})
			return {
						'name': _('Transfer all?'),
						'type': 'ir.actions.act_window',
						'view_type': 'form',
						'view_mode': 'form',
						'res_model': 'stock.checking.transfer.all',
						'views': [(view.id, 'form')],
						'view_id': view.id,
						'res_id': wiz.id,
						'target': 'new',
						'context': self.env.context,
					}


	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
	spc_line = fields.One2many('stock.picking.checking.line', 'spc_line_id', string='Line ids')


	@api.onchange('spc_line')
	def update_qty_in_line(self):
		for pick in self.spc_line:
			stock_pack_operation = self.env['stock.pack.operation'].search([('id', '=', pick.po_id)])
			if pick.qty_done > pick.product_qty:
				return {'warning': {'title': _('Napaka'), 'message': _('Imamo višek izdelkov.')}}
			stock_pack_operation.write({'qty_done': pick.qty_done})

	@api.multi
	def transfer(self):
		picking_ids = []
		SP_obj = self.env['stock.picking']
		stock_picking_checking_ids = self.spc_line
		for spci in stock_picking_checking_ids:
			picking_id = spci.sp_id
			if not picking_id in picking_ids:
				picking_ids.append(picking_id)
		return SP_obj.do_new_transfer_custom(picking_ids)

	@api.multi
	def transfer_all(self):
		picking_ids = []
		SP_obj = self.env['stock.picking']
		stock_picking_checking_ids = self.spc_line
		for spci in stock_picking_checking_ids:
			picking_id = spci.sp_id
			if not picking_id in picking_ids:
				picking_ids.append(picking_id)
		return SP_obj.do_new_transfer_all(picking_ids)


class StockPickingCheckingLine(models.Model):
	_name = 'stock.picking.checking.line'


	spc_line_id = fields.Many2one('stock.picking.checking', string='Order id', ondelete='cascade', readonly=True) #inverzna relacija
	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
	product_id = fields.Many2one('product.product', 'Product', readonly=True)
	product_qty = fields.Float('ToDo', readonly=True)
	qty_done = fields.Float('Done')
	name = fields.Char('Reference', readonly=True)
	location_dest_id = fields.Many2one('stock.location', "Destination Location Zone", readonly=True)
	origin = fields.Char('Source Document', readonly=True)
	sp_id = fields.Integer('SP_id', readonly=True)
	spo_id = fields.Integer('SPO_id', readonly=True)
	picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True)
	operation_id = fields.Many2one('stock.pack.operation', 'Stock pack operation', readonly=True)
	po_id = fields.Integer('operation_id', readonly=True)
	state = fields.Selection(selection=[
		('draft', 'Draft'),
		('cancel', 'Cancelled'),
		('waiting', 'Waiting Another Operation'),
		('confirmed', 'Waiting Availability'),
		('partially_available', 'Partially Available'),
		('assigned', 'Available'),
		('done', 'Done')], related='operation_id.state', readonly=True)


class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'


	@api.multi
	def get_data(self):
		stock_picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', 1)], limit=1).id
		stock_picking = self.env['stock.picking'].search([('picking_type_id', '=', stock_picking_type_id), ('state', 'in', ('assigned', 'partially_available', 'waiting'))])
		self.env.cr.execute("""delete from stock_picking_checking_line""")
		self.env.cr.execute("""delete from stock_picking_checking""")
		return stock_picking

	@api.multi
	def sort_and_create(self):
		res = self.get_data()
		data = {}
		vals = {}
		for r in res:
			for o in r.pack_operation_ids:
				if r.partner_id.id in data:
					data[r.partner_id.id].append({'product_id': o.product_id.id, 'product_qty': o.product_qty,
					                         'qty_done':  o.qty_done, 'name':r.name, 'operation_id': o.id, 'po_id': o.id,
											 'location_dest_id': o.location_dest_id.id,
											 'origin':  r.origin, 'state':  o.state, 'partner_id': r.partner_id.id,
											'picking_id': o.picking_id.id, 'sp_id': o.picking_id.id})
				else:
					data[r.partner_id.id] = [{'product_id': o.product_id.id, 'product_qty': o.product_qty,
					                         'qty_done': o.qty_done, 'name':r.name, 'operation_id': o.id, 'po_id': o.id,
											 'location_dest_id': o.location_dest_id.id,
											 'origin': r.origin, 'state': o.state, 'partner_id': r.partner_id.id,
											 'picking_id': o.picking_id.id, 'sp_id': o.picking_id.id}]

		SPCL_obj = self.env['stock.picking.checking.line']
		SPC_obj = self.env['stock.picking.checking']
		lines = []
		for d in data:
			lines = [(0, 0, {'product_id': a['product_id'], 'product_qty': a['product_qty'],
		                    'qty_done': a['qty_done'], 'name':a['name'],
		                    'location_dest_id': a['location_dest_id'],
		                    'origin': a['origin'], 'state': a['state'], 'partner_id': a['partner_id'],
		                    'picking_id': a['picking_id'], 'sp_id': a['sp_id'], 'operation_id': a['operation_id'],
		                     'po_id': a['po_id'],'spc_line_id': 1})for a in data[d]]

			vals.update({'partner_id': d, 'spc_line': lines})
			SPC_obj.create(vals)
			vals = {}
			lines = []

		search_view_id = self.env.ref('stock_picking_checking.stock_picking_checking_search', False).id

		return {
				'name': 'Check picking',
	            'view_type': 'form',
	            'view_mode': 'tree,form',
				'src_model': 'stock.picking.checking',
	            'res_model': 'stock.picking.checking',
	            'type': 'ir.actions.act_window',
	            'target': 'current',
				'id': self.id,
				'context': {},
			    'search_view_id': search_view_id,}

	@api.multi
	def update_taxes_id(self):
		product_template_instance = self.env['product.template']
		product_template_ids = product_template_instance.search([])
		product_template_ids = product_template_ids[640000:650000]
		dolzina = len(product_template_ids)
		i = 1
		#product_template_ids.write({'property_account_income_id':275, 'property_account_expense_id':292})
		for pt_id in product_template_ids:
			pt_id.write({'property_account_income_id':275, 'property_account_expense_id':292})
			#pt_id.write({'taxes_id': [(6, 0, [3])], 'supplier_taxes_id': [(6, 0, [14])]})
			i += 1
			percent = str(round(float(i) / float(dolzina) * 100, 2)) + "%"
			print percent
			print(str(i) + ' / ' + str(dolzina))


	@api.multi
	def update_expense_policy(self):
		operation = self.env['stock.pack.operation'].search([('id','=',16)])
		self.env.cr.execute("""SELECT id from product_template""")
		product_template_objects_ids = self.env.cr.fetchall()
		dolzina = len(product_template_objects_ids)
		i = 1
		for id in product_template_objects_ids:
			self.env.cr.execute(
				"""UPDATE product_template SET expense_policy = 'no', invoice_policy = 'delivery' where id = %(id)s""" % {'id': id[0]})
			print(str(i) + ' / ' + str(dolzina))
			i += 1