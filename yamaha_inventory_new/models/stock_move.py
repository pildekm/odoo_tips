# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class StockMove(models.Model):
	_inherit = 'stock.move'

	move_dest_partner = fields.Char('Customer', related='move_dest_id.picking_partner_id.name', store=True)


