## Imports
#from StringIO import StringIO
from odoo import api, fields, models, tools, _
#import base64
#import csv
#import logging
#import re
#from odoo.exceptions import ValidationError
#from odoo.osv import expression
#import odoo.addons.decimal_precision as dp

## Get the logger:
## Declare a temporary container:

class ProductProduct(models.Model):
	_inherit = 'product.product'


		
	def list_default_code_change(self, new_default_code ,all_products):
		print "tle sem"
		if new_default_code:
			element = self.search(['|',('active', '=', False),('active', '=', True),
								   ("default_code", "=",  new_default_code)],limit=1)
			#all_products += element[0]
			if element:
				#all_products.append(element[0])
				all_products.insert(0,element.id)
				if not new_default_code:
					return all_products
				product_info = element.read(["default_code","new_default_code"])[0]
				if product_info['new_default_code']:
					if product_info['default_code'] == product_info['new_default_code']:
						return
		   
					next_element = self.list_default_code_change(product_info['new_default_code'],all_products)
				else:
					print "all_products 1",all_products
					return all_products
		print "all_products 1",all_products
		return all_products
	#FIND FIRST ELEMENT ELEMENT AND APPEND IT
	def find_first(self, default_code ,all_products):

		print "default_code",default_code
		product_old_cat = self.search(['|',('active', '=', False),
									   ('active', '=', True),("new_default_code", "=",  default_code)],limit=1)
		print "product_old_cat",product_old_cat.id

		if not product_old_cat:

			product_old_cat = self.search(['|',('active', '=', False),
										   ('active', '=', True),("default_code", "=",  default_code)],limit=1)
			print "product_old_cat_inside",product_old_cat.id


			product_info = product_old_cat.read(["default_code","new_default_code"])[0]
 			print "product_info _22", product_info
			print "product_old_cat 2",product_old_cat.id
			#ta id odstrani ali ne
			all_products.insert(0,product_old_cat.id)
			print "product_info connected",product_info
			print "all_products",all_products

			if 'default_code' in product_info and 'new_default_code' in product_info:
				print "product_info['default_code'] ",product_info['default_code'] 
				print "product_info['new_default_code']",product_info['new_default_code']
				if product_info['default_code'] and product_info['new_default_code']:
					if product_info['default_code'] == product_info['new_default_code']:
						return

				if product_info['new_default_code']:
					print "ima new_default_code"
					first_element = self.list_default_code_change(product_info['new_default_code'],all_products)

		else:
			print "product_old_cat 3",product_old_cat.id

			product_info = product_old_cat.read(["default_code","new_default_code"])[0]

			#RECURSIVE
			print "product_info 4", product_info
			if 'default_code' in product_info and 'new_default_code' in product_info:
				if product_info['default_code'] and product_info['new_default_code']:
					if product_info['default_code'] == product_info['new_default_code']:
						return
				first_element = self.find_first(product_info['default_code'],all_products)
		return

	def get_related_default_code(self,  field_names=None):
		"""
		Returns all related product:
		"""
		## Copy the context:
		#context = self.context.copy()
		ids = self.ids
		## Declare the return value:
		result = {}
		print "self_ids",ids

		## If no IDs supplied, just return as is:
		if not ids:
			return result
  
		for id in ids:
			all_products = []
			#Zgodovina sprememb kataloskih
			product_info = self.read(["default_code","new_default_code","last_default_code"])[0]
	  		print "product_info",product_info
	  		result[id] = list(set([]))
	  		if product_info['default_code'] and product_info['new_default_code']:
				if product_info['default_code'] == product_info['new_default_code']:
					return
				related_default_code_list = self.find_first(product_info['default_code'],all_products)
			if product_info['last_default_code']:

				related_default_code_list = self.find_first(product_info['default_code'],all_products)
			#result[id] = all_products
			print "all_products", all_products
			if len(all_products) > 1:
				print "tle sem 1"
				result = all_products
			else:
				print "tle sem else"
				result = []
		
		self.related_default_code = result



	last_default_code =  fields.Char('Last Internal Reference', index=True)
	new_default_code = fields.Char('New Internal Reference', index=True)
	related_default_code = fields.One2many('product.product', string='Related Default Code',
										   compute='get_related_default_code')


	@api.one
	def button_update_stock(self):
		product_id = self.id
		self.env.cr.execute("""
					select  sq.id,
							sq.product_id,
							sq.qty,
							sq.location_id,
							sq.cost
					from stock_quant sq
					where sq.product_id = %(product_id)s """, {'product_id': product_id})
		res = self.env.cr.dictfetchall()
		int = 5
		for r in res:

			self.stock_availability= [(0,0,{'location_id': r['location_id'], 'cost': r['cost'], 'qty': r['qty']})]

		return

class product_template(models.Model):
	_inherit = "product.template"
	product_item_type_id = fields.Selection([
		('spare_parts', 'Spare Parts'),
		('accessories', 'Accessories'),
		('motor', 'Motor'),
		('liquidity', 'Liquidity'),]
		, 'Item type', help='Select a item type.', require=True)
	web_product = fields.Boolean(index=True, default=False, string='Web product',
							help="By unchecking the Web Product field you can disable a website product treatment.")
