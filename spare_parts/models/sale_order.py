# -*- coding: utf-8 -*-


from odoo import models, fields, api, exceptions, _
from odoo.osv import osv
from odoo.exceptions import UserError



class SaleOrder(models.Model):
	_inherit = 'sale.order'


    #
	# @api.one
	# def action_import_csv_quote(self):
	# 	print "tle sem"


		
class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	print ('derk')

	#izmjena na produktu
	#@api.multi



	#@api.onchange('product_id')
	@api.depends('product_id')
	def get_stock_quant(self):
		#izbrani id na formi
		product_id = self.product_id.id
		product_name = self.product_id.name
		related_default_code_obj = self.env['product.product'].search([('id','=',product_id)], limit=1).related_default_code
		product_ids = tuple(r.id for r in related_default_code_obj)
		uid = self._uid
		#ispraznimo tabelu za određeni uid
		self.env.cr.execute("""delete from sale_order_stock_quantity_wizz where create_uid = %(uid)s""", {'uid': uid})
		if product_ids:
			self.env.cr.execute("""
					select 	pp.id, 
							pp.default_code, 
							pp.last_default_code, 
							pp.new_default_code,
							pt.name,	
							sum(sq.qty) as qty,
							sq.location_id,
							sw.name as warehouse_name
					from product_product pp
					left join product_template pt on pt.id = pp.product_tmpl_id
					left join stock_quant sq on sq.product_id = pp.id
					left join stock_warehouse sw on sw.lot_stock_id = sq.location_id
					where pp.id in %(product_ids)s 
					group by sq.location_id, pp.id, pt.name, sq.qty, sw.name
					order by sq.location_id	""", {'product_ids': product_ids})

			res = self.env.cr.dictfetchall()
			product_ids=[]
			for r in res:
				vals = {'product_id': r['id'],
						'product_name': r['name'],
						'default_code':r['default_code'],
						'last_default_code':r['last_default_code'],
						'new_default_code':r['new_default_code'],
						'quantity':r['qty'],
						'location_id':r['location_id'],
						'location_name': r['warehouse_name'],}

				#self.update({'sale_order_stock_qty': (0,0,vals)})
				self.sale_order_stock_qty.create(vals)
				self.sale_order_stock_qty_wizz.create(vals)

			return

	#izmjena produkta iza odabira
	@api.onchange('sale_order_stock_qty_wizz')
	def get_selected_product(self):
		uid = self._uid
		if len(self.sale_order_stock_qty_wizz.ids) > 1:
			raise osv.except_osv(('Opozorilo'), ('Možno je izbrat samo eden izdelek!!!'))
		try:
			self.update({'product_id': self.sale_order_stock_qty_wizz.product_id,
						 'dt_stock':1,
						 'tm_stock':1})

		except UserError:
			pass
		return



	sale_order_stock_qty = fields.Many2many('sale.order.stock.quantity', string='Stock quantity', compute='get_stock_quant', store=True)
	sale_order_stock_qty_wizz = fields.Many2many('sale.order.stock.quantity.wizz', string='Quantity on hand')#, compute='get_stock_quant')
	dt_stock = fields.Integer('DT', readonly=True)
	tm_stock = fields.Integer('TM', readonly=True)

#This model is just for view no other Functionalities
class SaleOrderStockQuantity(models.Model):
	_name = 'sale.order.stock.quantity'

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
