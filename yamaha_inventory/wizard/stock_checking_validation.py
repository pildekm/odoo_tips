# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockCheckingValidation(models.TransientModel):
    _name = 'stock.checking.validation'
    _description = 'Stock checking validation'

    pick_id = fields.Many2one('stock.picking.checking')

    @api.multi
    def update(self):
		picking_ids = []
		SP_obj = self.env['stock.picking']
		partner_id = self.pick_id.partner_id.id
		stock_picking_checking_ids = self.env['stock.picking.checking'].search([('id','=',self.pick_id.id)]).spc_line
		for spci in stock_picking_checking_ids:
			picking_id = spci.sp_id
			if not picking_id in picking_ids:
				picking_ids.append(picking_id)

		for id in picking_ids:
			picking = SP_obj.search([('id', '=', id)])
			picking.do_new_transfer()



