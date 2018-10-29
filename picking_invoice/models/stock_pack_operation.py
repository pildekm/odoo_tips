# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare


class PackOperation(models.Model):
	_inherit = "stock.pack.operation"

	@api.multi
	def _compute_qty_done(self):
		picking_invoice_line_object = self.env['picking.invoice.line']
		for stock_pack_operation_line in self:


			picking_invoice_line_ids = picking_invoice_line_object.search([('pack_operation_product','=',stock_pack_operation_line.id)])

			current_qty_done = 0.0
			for picking_invoice_line in picking_invoice_line_ids:
				current_qty_done += picking_invoice_line.qty_done

			set_current_pack_operation_qty_done = current_qty_done
			stock_pack_operation_line.qty_done = set_current_pack_operation_qty_done
			stock_pack_operation_line.write({'qty_done': set_current_pack_operation_qty_done})



	# qty_done = fields.Float('Done', default=0.0, digits=dp.get_precision('Product Unit of Measure'),compute='_compute_qty_done',store=True)
