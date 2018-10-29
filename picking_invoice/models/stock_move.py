# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta
import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.addons.procurement.models import procurement
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class StockMoveSupplierRef(models.Model):
	_inherit = "stock.move"

	supplier_invoice_ref = fields.Integer(string="Supplier invoice ref", required=False)
	supplier_order_ref = fields.Integer(string="Supplier order ref", required=False)
	supplier_case_ref = fields.Integer(string="Supplier order ref", required=False)

	@api.multi
	def do_transfer_stock_move(self,stock_moves):
		""" Do transfer for stock_move"""
		stock_moves.stock_move_action_done()
		return True

	@api.multi
	def stock_move_action_done(self):
		""" Process completely the moves given and if all moves are done, it will finish the picking. """
		self.filtered(lambda move: move.state == 'draft').action_confirm()

		Uom = self.env['product.uom']
		Quant = self.env['stock.quant']

		pickings = self.env['stock.picking']
		procurements = self.env['procurement.order']
		operations = self.env['stock.pack.operation']

		remaining_move_qty = {}

		for move in self:
			if move.picking_id:
				pickings |= move.picking_id
			remaining_move_qty[move.id] = move.product_qty
			for link in move.linked_move_operation_ids:
				operations |= link.operation_id
				pickings |= link.operation_id.picking_id

		# Sort operations according to entire packages first, then package + lot, package only, lot only
		operations = operations.sorted(
			key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (
			x.pack_lot_ids and -1 or 0))

		for operation in operations:

			# product given: result put immediately in the result package (if False: without package)
			# but if pack moved entirely, quants should not be written anything for the destination package
			quant_dest_package_id = operation.product_id and operation.result_package_id.id or False
			entire_pack = not operation.product_id and True or False

			# compute quantities for each lot + check quantities match
			lot_quantities = dict((pack_lot.lot_id.id, operation.product_uom_id._compute_quantity(pack_lot.qty,
			                                                                                      operation.product_id.uom_id)
			                       ) for pack_lot in operation.pack_lot_ids)

			qty = operation.product_qty
			if operation.product_uom_id and operation.product_uom_id != operation.product_id.uom_id:
				qty = operation.product_uom_id._compute_quantity(qty, operation.product_id.uom_id)
			if operation.pack_lot_ids and float_compare(sum(lot_quantities.values()), qty,
			                                            precision_rounding=operation.product_id.uom_id.rounding) != 0.0:
				raise UserError(_(
					'You have a difference between the quantity on the operation and the quantities specified for the lots. '))

			quants_taken = []
			false_quants = []
			lot_move_qty = {}

			prout_move_qty = {}
			for link in operation.linked_move_operation_ids:
				prout_move_qty[link.move_id] = prout_move_qty.get(link.move_id, 0.0) + link.qty

			# Process every move only once for every pack operation
			for move in prout_move_qty.keys():
				# TDE FIXME: do in batch ?
				move.check_tracking(operation)

				# TDE FIXME: I bet the message error is wrong
				# if not remaining_move_qty.get(move.id):
				# 	raise UserError(_(
				# 		"The roundings of your unit of measure %s on the move vs. %s on the product don't allow to do these operations or you are not transferring the picking at once. ") % (
				# 	                move.product_uom.name, move.product_id.uom_id.name))

				if not operation.pack_lot_ids:
					preferred_domain_list = [[('reservation_id', '=', move.id)], [('reservation_id', '=', False)],
					                         ['&', ('reservation_id', '!=', move.id),
					                          ('reservation_id', '!=', False)]]
					quants = Quant.quants_get_preferred_domain(
						prout_move_qty[move], move, ops=operation, domain=[('qty', '>', 0)],
						preferred_domain_list=preferred_domain_list)
					Quant.quants_move(quants, move, operation.location_dest_id, location_from=operation.location_id,
					                  lot_id=False, owner_id=operation.owner_id.id,
					                  src_package_id=operation.package_id.id,
					                  dest_package_id=quant_dest_package_id, entire_pack=entire_pack)
				else:
					# Check what you can do with reserved quants already
					qty_on_link = prout_move_qty[move]
					rounding = operation.product_id.uom_id.rounding
					for reserved_quant in move.reserved_quant_ids:
						if (reserved_quant.owner_id.id != operation.owner_id.id) or (
							reserved_quant.location_id.id != operation.location_id.id) or \
								(reserved_quant.package_id.id != operation.package_id.id):
							continue
						if not reserved_quant.lot_id:
							false_quants += [reserved_quant]
						elif float_compare(lot_quantities.get(reserved_quant.lot_id.id, 0), 0,
						                   precision_rounding=rounding) > 0:
							if float_compare(lot_quantities[reserved_quant.lot_id.id], reserved_quant.qty,
							                 precision_rounding=rounding) >= 0:
								lot_quantities[reserved_quant.lot_id.id] -= reserved_quant.qty
								quants_taken += [(reserved_quant, reserved_quant.qty)]
								qty_on_link -= reserved_quant.qty
							else:
								quants_taken += [(reserved_quant, lot_quantities[reserved_quant.lot_id.id])]
								lot_quantities[reserved_quant.lot_id.id] = 0
								qty_on_link -= lot_quantities[reserved_quant.lot_id.id]
					lot_move_qty[move.id] = qty_on_link

				remaining_move_qty[move.id] -= prout_move_qty[move]

			# Handle lots separately
			if operation.pack_lot_ids:
				# TDE FIXME: fix call to move_quants_by_lot to ease understanding
				self._move_quants_by_lot(operation, lot_quantities, quants_taken, false_quants, lot_move_qty,
				                         quant_dest_package_id)

			# Handle pack in pack
			if not operation.product_id and operation.package_id and operation.result_package_id.id != operation.package_id.parent_id.id:
				operation.package_id.sudo().write({'parent_id': operation.result_package_id.id})

		# Check for remaining qtys and unreserve/check move_dest_id in
		move_dest_ids = set()
		for move in self:
			if float_compare(remaining_move_qty[move.id], 0,
			                 precision_rounding=move.product_id.uom_id.rounding) > 0:  # In case no pack operations in picking
				move.check_tracking(False)  # TDE: do in batch ? redone ? check this

				preferred_domain_list = [[('reservation_id', '=', move.id)], [('reservation_id', '=', False)],
				                         ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]]
				quants = Quant.quants_get_preferred_domain(
					remaining_move_qty[move.id], move, domain=[('qty', '>', 0)],
					preferred_domain_list=preferred_domain_list)
				Quant.quants_move(
					quants, move, move.location_dest_id,
					lot_id=move.restrict_lot_id.id, owner_id=move.restrict_partner_id.id)

			# If the move has a destination, add it to the list to reserve
			if move.move_dest_id and move.move_dest_id.state in ('waiting', 'confirmed'):
				move_dest_ids.add(move.move_dest_id.id)

			if move.procurement_id:
				procurements |= move.procurement_id

			# unreserve the quants and make them available for other operations/moves
			move.quants_unreserve()

		# Check the packages have been placed in the correct locations
		self.mapped('quant_ids').filtered(lambda quant: quant.package_id and quant.qty > 0).mapped(
			'package_id')._check_location_constraint()

		# set the move as done
		self.write({'state': 'done', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
		procurements.check()
		# assign destination moves
		if move_dest_ids:
			# TDE FIXME: record setise me
			self.browse(list(move_dest_ids)).action_assign_stock_move()

		pickings.filtered(lambda picking: picking.state == 'done' and not picking.date_done).write(
			{'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

		return True

	@api.multi
	def action_assign_stock_move(self, no_prepare=False):
		""" Checks the product type and accordingly writes the state. """
		# TDE FIXME: remove decorator once everything is migrated
		# TDE FIXME: clean me, please
		main_domain = {}

		Quant = self.env['stock.quant']
		Uom = self.env['product.uom']
		moves_to_assign = self.env['stock.move']
		moves_to_do = self.env['stock.move']
		operations = self.env['stock.pack.operation']
		ancestors_list = {}

		# work only on in progress moves
		moves = self.filtered(lambda move: move.state in ['confirmed', 'waiting', 'assigned'])
		moves.filtered(lambda move: move.reserved_quant_ids).do_unreserve()
		for move in moves:
			if move.location_id.usage in ('supplier', 'inventory', 'production'):
				moves_to_assign |= move
				# TDE FIXME: what ?
				# in case the move is returned, we want to try to find quants before forcing the assignment
				if not move.origin_returned_move_id:
					continue
			# if the move is preceeded, restrict the choice of quants in the ones moved previously in original move
			ancestors = move.find_move_ancestors()
			if move.product_id.type == 'consu' and not ancestors:
				moves_to_assign |= move
				continue
			else:
				moves_to_do |= move

				# we always search for yet unassigned quants
				main_domain[move.id] = [('reservation_id', '=', False), ('qty', '>', 0)]

				ancestors_list[move.id] = True if ancestors else False
				if move.state == 'waiting' and not ancestors:
					# if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
					main_domain[move.id] += [('id', '=', False)]
				elif ancestors:
					main_domain[move.id] += [('history_ids', 'in', ancestors.ids)]

				# if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
				if move.origin_returned_move_id:
					main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
				for link in move.linked_move_operation_ids:
					operations |= link.operation_id

		# Check all ops and sort them: we want to process first the packages, then operations with lot then the rest
		operations = operations.sorted(
			key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (
				x.pack_lot_ids and -1 or 0))
		for ops in operations:
			# TDE FIXME: this code seems to be in action_done, isn't it ?
			# first try to find quants based on specific domains given by linked operations for the case where we want to rereserve according to existing pack operations
			if not (ops.product_id and ops.pack_lot_ids):
				for record in ops.linked_move_operation_ids:
					move = record.move_id
					if move.id in main_domain:
						qty = record.qty
						domain = main_domain[move.id]
						if qty:
							quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, domain=domain,
							                                           preferred_domain_list=[])
							Quant.quants_reserve(quants, move, record)
			else:
				lot_qty = {}
				rounding = ops.product_id.uom_id.rounding
				for pack_lot in ops.pack_lot_ids:
					lot_qty[pack_lot.lot_id.id] = ops.product_uom_id._compute_quantity(pack_lot.qty,
					                                                                   ops.product_id.uom_id)
				for record in ops.linked_move_operation_ids:
					move_qty = record.qty
					move = record.move_id
					domain = main_domain[move.id]
					for lot in lot_qty:
						if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(move_qty,
						                                                                                     0,
						                                                                                     precision_rounding=rounding) > 0:
							qty = min(lot_qty[lot], move_qty)
							quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot, domain=domain,
							                                           preferred_domain_list=[])
							Quant.quants_reserve(quants, move, record)
							lot_qty[lot] -= qty
							move_qty -= qty

		# Sort moves to reserve first the ones with ancestors, in case the same product is listed in
		# different stock moves.
		for move in sorted(moves_to_do, key=lambda x: -1 if ancestors_list.get(x.id) else 0):
			# then if the move isn't totally assigned, try to find quants without any specific domain
			if move.state != 'assigned' and not self.env.context.get('reserve_only_ops'):
				qty_already_assigned = move.reserved_availability
				qty = move.product_qty - qty_already_assigned

				quants = Quant.quants_get_preferred_domain(qty, move, domain=main_domain[move.id],
				                                           preferred_domain_list=[])
				Quant.quants_reserve(quants, move)

		# force assignation of consumable products and incoming from supplier/inventory/production
		# Do not take force_assign as it would create pack operations
		if moves_to_assign:
			moves_to_assign.write({'state': 'assigned'})
		if not no_prepare:
			self.check_recompute_pack_op()
