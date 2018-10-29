# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockCheckingValidation(models.TransientModel):
    _name = 'stock.checking.validation'
    _description = 'Stock checking validation'

    pick_id = fields.Many2one('stock.picking.checking')

    @api.multi
    def transfer(self,pick_id = False):
	    picking_ids = []
	    if type(pick_id) is dict:
		    pick_id = self.pick_id.id

	    pick_id = int(pick_id)
	    SP_obj = self.env['stock.picking']
	    stock_picking_checking_ids = self.env['stock.picking.checking'].search([('id', '=' ,pick_id)]).spc_line
	    for spci in stock_picking_checking_ids:
		    picking_id = spci.sp_id
		    if not picking_id in picking_ids:
			    picking_ids.append(picking_id)
	    return SP_obj.do_new_transfer_custom(picking_ids)



