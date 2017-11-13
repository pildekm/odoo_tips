# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockCheckingValidation(models.TransientModel):
    _name = 'stock.checking.validation'
    _description = 'Stock checking validation'
    pick_id = fields.Many2one('stock.picking.checking')

    @api.multi
    def update(self):
	    SP_obj = self.env['stock.picking']
	    partner_id = self.pick_id.partner_id.id

	    for line in self.pick_id.spc_line:
		    picking = SP_obj.search([('id','=',line.picking_id.id),('partner_id','=',partner_id)])
		    picking.do_transfer()
		    #line.qty_done = line.product_qty

