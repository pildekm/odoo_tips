# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	move_lines_in = fields.One2many('stock.move', 'picking_id', string="Stock Moves", related='move_lines', store=True)

	# ----------------------metode za končaj vse-----------------------------------------------

	#custom metoda validiraj vse
	@api.multi
	def do_new_transfer_all(self, picking_ids):
		pickings = []
		for pick_id in picking_ids:
			pick = self.env['stock.picking'].search([('id', '=', pick_id)])
			#---pušta samo pickinge bez vrijednosti u qty_done
			if all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
				pickings.append(pick)

		if not pickings:
			raise UserError(_('Ni mogoče validirat vse izdelkov hkrati !!!'))

		for pick in pickings:
			if pick.state == 'done':
				raise UserError(_('The pick is already validated'))
			pack_operations_delete = self.env['stock.pack.operation']
			if not pick.move_lines and not pick.pack_operation_ids:
				raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
			# In draft or with no pack operations edited yet, ask if we can just do everything
			if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
				# If no lots when needed, raise error
				picking_type = pick.picking_type_id
				if (picking_type.use_create_lots or picking_type.use_existing_lots):
					for pack in pick.pack_operation_ids:
						if pack.product_id and pack.product_id.tracking != 'none':
							raise UserError(
								_('Some products require lots/serial numbers, so you need to specify those first!'))
				self.process_done(pick)
			else:
				raise UserError(_('Ni mogoče validirat vse izdelkov hkrati !!!'))

			for operation in pick.pack_operation_ids:
				if operation.qty_done < 0:
					raise UserError(_('No negative quantities allowed'))
				if operation.qty_done > 0:
					operation.write({'product_qty': operation.qty_done})
				else:
					pack_operations_delete |= operation
			if pack_operations_delete:
				pack_operations_delete.unlink()
		self.do_transfer()


	@api.multi
	def process_done(self, pick):
		# If still in draft => confirm and assign
		if pick.state == 'draft':
			pick.action_confirm()
			if pick.state != 'assigned':
				pick.action_assign()
				if pick.state != 'assigned':
					raise UserError(_(
						"Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
		for pack in pick.pack_operation_ids:
			if pack.product_qty > 0:
				pack.write({'qty_done': pack.product_qty})
				stock_picking_checking_line = self.env['stock.picking.checking.line'].search([('po_id', '=', pack.id)])
				stock_picking_checking_line.write({'qty_done': pack.product_qty})
			else:
				pack.unlink()
		pick.do_transfer()
#---------------------------------------konec končaj vse---------------------------------------------

# -----------------------metode za backorder---------------------------------

	#do_new_transfer za back oreder

	@api.multi
	def do_new_transfer_custom(self, picking_ids):
		pickings = []
		for pick_id in picking_ids:
			pick = self.env['stock.picking'].search([('id', '=', pick_id)])
			#---pušta samo picking s vrijednostima u qty_done
			if not all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
				pickings.append(pick)

		for pick in pickings:
			if pick.state == 'done':
				raise UserError(_('The pick is already validated'))
			pack_operations_delete = self.env['stock.pack.operation']
			if not pick.move_lines and not pick.pack_operation_ids:
				raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))

			# Check backorder should check for other barcodes
			if pick.check_backorder():
				self._process_backorder(pick)

			for operation in pick.pack_operation_ids:
				if operation.qty_done < 0:
					raise UserError(_('No negative quantities allowed'))
				if operation.qty_done > 0:
					operation.write({'product_qty': operation.qty_done})
				else:
					pack_operations_delete |= operation
			if pack_operations_delete:
				pack_operations_delete.unlink()
		self.do_transfer()

	@api.multi
	def _process_backorder(self, pick):
		operations_to_delete = pick.pack_operation_ids.filtered(lambda o: o.qty_done <= 0)
		for pack in pick.pack_operation_ids - operations_to_delete:
			stock_picking_checking_line = self.env['stock.picking.checking.line'].search([('po_id', '=', pack.id)])
			pack.product_qty = pack.qty_done
			stock_picking_checking_line.write({'qty_done': pack.product_qty})
		operations_to_delete.unlink()
		pick.do_transfer()

	@api.multi
	def process_backorder(self, pick):
		self._process_backorder(pick)

#-----------------------------------------konec backorder------------------------------------------------------------------------------

	@api.multi
	def state_available(self):
		lines_pop = [(0, 0, {'product_uom_id': ml.product_uom.id, 'product_id': ml.product_id.id, 'product_qty': ml.product_qty,
		                     'qty_done': 0, 'ordered_qty': ml.product_qty,
		                     'origin': ml.origin, 'partner_id': ml.partner_id.id,
		                     'location_dest_id': ml.location_dest_id.id, 'location_id': ml.location_id.id,
		                     'picking_id': ml.picking_id.id, 'state': 'assigned'}) for ml in self.move_lines]

		lines_ml = [(1, ml.id, {'state': 'assigned'}) for ml in self.move_lines]

		self.write({'pack_operation_product_ids': lines_pop, 'state': 'assigned', 'move_lines': lines_ml})

