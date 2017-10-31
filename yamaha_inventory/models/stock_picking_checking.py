# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class StockPickingChecking(models.Model):
	_name = 'stock.picking.checking'

	partner_id = fields.Many2one('res.partner', 'Partner')
	product_id = fields.Many2one('product.product', 'Product')
	product_qty = fields.Float('ToDo')
	qty_done = fields.Float('Done')
	name = fields.Char('Reference',)
	location_dest_id = fields.Many2one('stock.location', "Destination Location Zone")
	origin = fields.Char('Source Document')
	state = fields.Char('State')
	sp_id = fields.Integer('SP_id')
	spo_id = fields.Integer('SPO_id')
	picking_id = fields.Integer('Picking_id')

class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	@api.multi
	def get_data(self):
		self.env.cr.execute("""delete from stock_picking_checking""")
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
		SPC_obj = self.env['stock.picking.checking']
		for r in res:
			SPC_obj.create({'product_id': r['product_id'], 'product_qty':r['product_qty'],
			                'qty_done': r['qty_done'], 'name':r['name'],
			                'location_dest_id': r['location_dest_id'],
			                'origin': r['origin'], 'state': r['state'], 'partner_id': r['partner_id'],
			                'sp_id': r['sp_id'], 'spo_id': r['spo_id'], 'picking_id': r['picking_id'], })

		return {
				'name': 'Check picking',
	            'view_type': 'tree',
	            'view_mode': 'tree',
	            'res_model': 'stock.picking.checking',
	            'type': 'ir.actions.act_window',
	            'res_id': self.id,
	            'target': 'current', }
