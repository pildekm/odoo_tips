# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	move_lines_in = fields.One2many('stock.move', 'picking_id', string="Stock Moves", related='move_lines', store=True)