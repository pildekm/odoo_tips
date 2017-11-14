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
			else:
				return {'warning': {'title': _('Napaka'), 'message': _('Skenirani izdelek ni na listi.')}}

		# res = super(StockPickingChecking).on_barcode_scanned(barcode)
		# return res

	@api.multi
	def validate(self):
		for pick in self:
			view = self.env.ref('yamaha_inventory_new.stock_checking_validation_view')
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
	def unvalidate(self):
		for line in self.spc_line:
			line.qty_done = 0

	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
	spc_line = fields.One2many('stock.picking.checking.line', 'spc_line_id', string='Line ids')
	qty = fields.Float('Qty')
	# barcode = fields.Char('Barcode', copy=False, oldname='loc_barcode')
	# barcode_nomenclature_id = fields.Many2one('barcode.nomenclature', 'Barcode Nomenclature')

	@api.onchange('spc_line')
	def update_qty_in_line(self):
		picking_id = self.spc_line.picking_id.id
		stock_pack_operation = self.env['stock.pack.operation'].search([('picking_id', '=', picking_id)])
		if self.spc_line.qty_done > self.spc_line.product_qty:
			return {'warning': {'title': _('Napaka'), 'message': _('Imamo višek izdelkov.')}}
		stock_pack_operation.write({'qty_done': self.spc_line.qty_done})

	# @api.model
	# def default_get(self, fields):
	# 	res = super(StockPickingChecking, self).default_get(fields)
	# 	if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
	# 		res['barcode'] = res['complete_name']
	# 	return res

	@api.multi
	def transfer(self):
		picking_ids = []
		SP_obj = self.env['stock.picking']
		stock_picking_checking_ids = self.spc_line
		for spci in stock_picking_checking_ids:
			picking_id = spci.sp_id
			if not picking_id in picking_ids:
				picking_ids.append(picking_id)

		for id in picking_ids:
			picking = SP_obj.search([('id', '=', id)])
			picking.do_new_transfer()

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
	state = fields.Char('State', readonly=True)
	sp_id = fields.Integer('SP_id', readonly=True)
	spo_id = fields.Integer('SPO_id', readonly=True)
	picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True)


class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	@api.multi
	def get_data(self):

		stock_picking_type_id = self.env['stock.picking.type'].search([('code','=','outgoing'),('warehouse_id','=',1)], limit=1).id
		stock_picking = self.env['stock.picking'].search([('picking_type_id','=',stock_picking_type_id),('state','in',('assigned','partially_available'))])
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
					                         'qty_done':  o.qty_done, 'name':r.name,
											 'location_dest_id': o.location_dest_id.id,
											 'origin':  r.origin, 'state':  o.state, 'partner_id': r.partner_id.id,
											'picking_id': o.picking_id.id, 'sp_id': o.picking_id.id})
				else:
					data[r.partner_id.id] = [{'product_id': o.product_id.id, 'product_qty': o.product_qty,
					                         'qty_done': o.qty_done, 'name':r.name,
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
		                    'picking_id': a['picking_id'], 'sp_id': a['sp_id'], 'spc_line_id': 1})for a in data[d]]

			vals.update({'partner_id': d, 'spc_line': lines})
			SPC_obj.create(vals)
			vals = {}
			lines = []

		search_view_id = self.env.ref('yamaha_inventory_new.stock_picking_checking_search', False).id

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
