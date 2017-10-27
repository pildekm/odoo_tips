# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class StockMove(models.Model):
	_inherit = 'stock.move'

	#picking_partner = fields.Char('Customer', related='picking_partner_id.name', store=True)
	move_dest_partner = fields.Char('Customer', related='move_dest_id.picking_partner_id.name', store=True)


	# @api.multi
	# def _set_default_price_moves(self):
	# 	res = super(StockMove, self)._set_default_price_moves()
	# 	return res

