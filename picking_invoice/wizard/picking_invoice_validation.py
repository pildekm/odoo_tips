# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PickingInvoiceValidation(models.TransientModel):
    _name = 'picking.invoice.validation'
    _description = 'Stock checking validation'

    picking_invoice_id = fields.Many2one('picking.invoice')

    @api.multi
    def transfer(self):

	    stock_pack_operation_object = self.env['stock.pack.operation']
	    stock_picking_object = self.env['stock.picking']
	    ids = []
	    for picking_invoice_line in self.picking_invoice_id.order_line:
		    ids.append(picking_invoice_line.pack_operation_product.id)

	    stock_picking_ids = stock_picking_object.search([('pack_operation_product_ids', 'in', ids)])
	    result = stock_picking_ids.do_new_transfer_invoice_picking()

	    if result:
		    self.picking_invoice_id.state = 'done'

    @api.multi
    def transfer_from_ui(self,picking_invoice_id):
	    picking_invoice_id = int(picking_invoice_id)
	    new_transfer = self.create({'picking_invoice_id':picking_invoice_id})
	    new_transfer.transfer()

