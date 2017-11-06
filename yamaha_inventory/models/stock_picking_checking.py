# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class StockPickingChecking(models.Model):
	_name = 'stock.picking.checking1'

	partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
	spc_line = fields.One2many('stock.picking.checking.line1', 'spc_line_id', string='Line ids')

class StockPickingCheckingLine(models.Model):
	_name = 'stock.picking.checking.line1'

	spc_line_id = fields.Many2one('stock.picking.checking1', string='Order id', ondelete='cascade', readonly=True) #inverzna relacija
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
	picking_id = fields.Integer('Picking_id', readonly=True)



class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	@api.multi
	def get_data(self):
		self.env.cr.execute("""delete from stock_picking_checking_line1""")
		self.env.cr.execute("""delete from stock_picking_checking1""")
		self.env.cr.execute("""
			select  sp.id as sp_id,
			        spo.id as spo_id,
			        spo.picking_id,
					sp.partner_id,
					sp.name,
					sp.location_dest_id,
					sp.origin,
					sp.state,
					spo.product_id,
					spo.product_qty,
					spo.qty_done
				from stock_picking sp
				left join stock_pack_operation spo on spo.picking_id = sp.id
				where state like 'assigned'
				order by sp.partner_id""")
		res = self.env.cr.dictfetchall()
		return res

	@api.multi
	def sort_and_create(self):
		res = self.get_data()
		data = {}
		vals = {}
		for r in res:
			if r['partner_id'] in data:
				data[r['partner_id']].append({'product_id': r['product_id'], 'product_qty':r['product_qty'],
				                         'qty_done': r['qty_done'], 'name':r['name'],
										 'location_dest_id': r['location_dest_id'],
										 'origin': r['origin'], 'state': r['state'], 'partner_id': r['partner_id'],
										 'sp_id': r['sp_id'], 'spo_id': r['spo_id'], 'picking_id': r['picking_id'],})
			else:
				data[r['partner_id']] = [{'product_id': r['product_id'], 'product_qty':r['product_qty'],
				                         'qty_done': r['qty_done'], 'name':r['name'],
										 'location_dest_id': r['location_dest_id'],
										 'origin': r['origin'], 'state': r['state'], 'partner_id': r['partner_id'],
										 'sp_id': r['sp_id'], 'spo_id': r['spo_id'], 'picking_id': r['picking_id'],}]

		SPCL_obj = self.env['stock.picking.checking.line1']
		SPC_obj = self.env['stock.picking.checking1']
		lines = []
		for d in data:
			lines = [(0, 0, {'product_id': a['product_id'], 'product_qty': a['product_qty'],
		                    'qty_done': a['qty_done'], 'name':a['name'],
		                    'location_dest_id': a['location_dest_id'],
		                    'origin': a['origin'], 'state': a['state'], 'partner_id': a['partner_id'],
		                    'sp_id': a['sp_id'], 'spo_id': a['spo_id'], 'picking_id': a['picking_id'],
			                'spc_line_id': 1})for a in data[d]]

			vals.update({'partner_id': d, 'spc_line': lines})
			SPC_obj.create(vals)
			vals = {}
			lines = []
		# for r in res:
		# 	SPCL_obj.create({'product_id': r['product_id'], 'product_qty':r['product_qty'],
		# 	                'qty_done': r['qty_done'], 'name':r['name'],
		# 	                'location_dest_id': r['location_dest_id'],
		# 	                'origin': r['origin'], 'state': r['state'], 'partner_id': r['partner_id'],
		# 	                'sp_id': r['sp_id'], 'spo_id': r['spo_id'], 'picking_id': r['picking_id'], })
		# 	SPC_obj.create({'partner_id': r['partner_id'], 'spc_line_ids': lines})
		# lines = [(0,0, {'product_id': r['product_id'], 'product_qty':r['product_qty'],
		#                     'qty_done': r['qty_done'], 'name':r['name'],
		#                      'location_dest_id': r['location_dest_id'],
		#                      'origin': r['origin'], 'state': r['state'], 'partner_id': r['partner_id'],
		#                      'sp_id': r['sp_id'], 'spo_id': r['spo_id'], 'picking_id': r['picking_id'], }) for r in res]
		#
		#
		# 	# stock_picking_checking_search: id = 12798
		search_view_id = self.env.ref('yamaha_inventory.stock_picking_checking_search1', False).id
		#
		return {
				'name': 'Check picking',
	            'view_type': 'form',
	            'view_mode': 'tree,form',
				'src_model': 'stock.picking.checking1',
	            'res_model': 'stock.picking.checking1',
	            'type': 'ir.actions.act_window',
	            'target': 'current',
				'id': self.id,
				'context': {},
			    'search_view_id': search_view_id,}
