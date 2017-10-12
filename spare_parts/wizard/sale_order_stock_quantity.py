# -*- coding: utf-8 -*-


from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
from odoo.exceptions import UserError

class SaleOrderStockQuantity(models.TransientModel):
	_name = 'sale.order.stock.quantity.wizz'

	sosq_id = fields.Many2one('sale.order.stock.quantity', string='Stock quantity')
	product_id = fields.Integer('Product', size=10)
	default_code = fields.Char('Internal reference number')
	last_default_code = fields.Char('Last internal reference number')
	new_default_code = fields.Char('New internal referenmce number')
	quantity = fields.Integer('Quantity')
	product_name = fields.Char('Product name')
	location_id = fields.Char('Location id')
	location_name = fields.Char('Location name')

	@api.multi
	def name_get(self):
		res = []
		name = ''
		for r in self:
			name = '['+r.default_code+']'+' '+ r.product_name +' '+str(r.location_name) +' '+ str(r.quantity)
			rez = (r.id, name)
			res.append(rez)
		return res

