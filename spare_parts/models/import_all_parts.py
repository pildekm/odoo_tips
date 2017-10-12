from openerp.osv import fields, osv
import time
import datetime
import csv
import psycopg2
from openerp import tools, fields, models, exceptions, api, _
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from os import getenv
import pymssql
import sys
import os
import base64
import cStringIO
import urllib
import json
from openerp.addons.website.models.website import slug
from openerp import SUPERUSER_ID





#04 class odoo_update_csv
class spare_parts_importer(models.TransientModel):
	_name = 'spare_parts.importer'
	_description = 'Spare parts importer'
	

	_defaults = {
		'name': "Spare Parts Importer",
	}
	
	def import_spare_parts(self, cr, uid, ids, context=None,data_values=None):
		start2 = time.time()
		allow_update = True
		product_product_object = self.pool.get('product.product')
		product_template_object = self.pool.get('product.template')
		#print "data_values",data_values
		product_product_ids = product_product_object.search(cr, SUPERUSER_ID, [('default_code', '=', data_values['default_code'])], limit=1)
		product_product = product_product_object.browse(cr, SUPERUSER_ID, product_product_ids, context=context)
		if allow_update:
			if product_product:
				#if #print data_values['default_code'] =
				#print data_values['default_code']
				print "Obstaja - UPDETAM ..."
				#print "product_product", product_product
				product_template_link_id = product_product['product_tmpl_id']['id']
				product_template_data = {}
				product_template_data['state'] = data_values['state']
				#product_template_data['product_brand_id'] = data_values['product_brand_id']
				#product_template_data['weight_net'] = data_values['weight_net']
				product_template_data['product_item_type_id'] = data_values['product_item_type_id']
				product_product_data = {}
				if (data_values['new_default_code'] != False and data_values['new_default_code'] != ""):
					product_product_data['new_default_code'] = data_values['new_default_code']
				if (data_values['last_default_code'] != False and data_values['last_default_code'] != ""):
					product_product_data['last_default_code'] = data_values['last_default_code']

				print "product_template_link_id",product_template_link_id
				print "template_data",product_template_data
				print "product_product_id", product_product.id
				print "product_product_data", product_product_data
				product_template_object.write(cr, SUPERUSER_ID, product_template_link_id, product_template_data, context=context)
				cr.commit()
				
				print len(product_product_data)
				if (len(product_product_data)>0):
					print "kao write"
					product_product_object.write(cr, SUPERUSER_ID, product_product.id, product_product_data, context=context)
					
				cr.commit()
				
			else:
				print "Ne obstaja - NEW PRODUCT"
				product_template_data = {}
				product_template_data['uom_id'] = data_values['uom_id']
				product_template_data['uom_po_id'] = data_values['uom_po_id']
				product_template_data['name'] = data_values['name']
				product_template_data['categ_id'] = data_values['categ_id']
				product_template_data['type'] = data_values['type']
				product_template_data['purchase_line_warn'] = data_values['purchase_line_warn']
				product_template_data['sale_line_warn'] = data_values['sale_line_warn']
				product_template_data['product_item_type_id'] = data_values['product_item_type_id']
				product_template_data['active'] = data_values['active']
				if (data_values['state'] != False and data_values['state'] != ""):
					product_template_data['state'] = data_values['state']
				#product_template_data['product_brand_id'] = data_values['product_brand_id']
				#product_template_data['weight_net'] = data_values['weight_net']
				product_template_id = product_template_object.create(cr, SUPERUSER_ID, product_template_data)
				product_product_data = {}
				product_product_data['write_uid'] = 1
				product_product_data['product_tmpl_id'] = product_template_id
				product_product_data['name_template'] =data_values['name']
				product_product_data['default_code'] =data_values['default_code']
				product_product_data['active'] =data_values['active']
				if (data_values['new_default_code'] != False and data_values['new_default_code'] != ""):
					product_product_data['new_default_code'] = data_values['new_default_code']
				if (data_values['last_default_code'] != False and data_values['last_default_code'] != ""):
					product_product_data['last_default_code'] = data_values['last_default_code']
				product_template_id = product_product_object.create(cr, SUPERUSER_ID, product_product_data)
			cr.commit()
		end2 = time.time()
		elapsed2 = end2 - start2
		print "---Konec enega ( Cas:", str(round(elapsed2)),"min  ) ---"
		return True
	def import_spare_parts_db(self, cr, uid, ids, context=None,data_values=None):
		allow_update = True
		if data_values['default_code'] != False and data_values['default_code'] != 'default_code' and data_values['default_code'] != '000000000000':
			cur.execute("SELECT id FROM product_product  WHERE default_code = %s ",[data_values['default_code']])
				#print "Number of rows updated: %d" % cur.rowcount
			#print "data", data_values
			try:

					(codeid,) = cur.fetchone()
					#print (codeid,)
					print codeid
					if allow_update and codeid:
						#if print data_values['default_code'] =
						print data_values['default_code']
						#print data_values['new_default_code']
						print "Obstaja - UPDETAM ..."

						cur.execute("SELECT product_tmpl_id FROM product_product  WHERE id = %s ",[codeid])
						(product_template_id,) = cur.fetchone()
						#print  product_template_id
						cur.execute("SELECT web_product FROM product_template  WHERE id = %s ",[product_template_id])
						(web_product,) = cur.fetchone()
						#print web_product
						cur.execute("UPDATE product_template SET  state = %s,product_brand_id=%s,weight_net=%s,product_item_type_id=%s WHERE id = %s ",(data_values['state'],data_values['product_brand_id'],data_values['weight_net'],data_values['product_item_type_id'],product_template_id))
						cur.execute("UPDATE product_product SET  new_default_code = %s,last_default_code = %s WHERE id = %s ",(data_values['last_default_code'],codeid))

							#print codeid
					return


			except:
					print data_values['default_code']
					print "Ne obstaja - NEW PRODUCT"
				
					#print data_values
					cur.execute("INSERT INTO product_template (uom_id,uom_po_id,name,categ_id,type,purchase_line_warn,sale_line_warn,product_item_type_id,active,state,product_brand_id,weight_net) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id", [data_values['uom_id'],data_values['uom_po_id'],data_values['name'],data_values['categ_id'],data_values['type'],data_values['purchase_line_warn'],data_values['sale_line_warn'],data_values['product_item_type_id'],data_values['active'],data_values['state'],data_values['product_brand_id'],data_values['weight_net']])
					#cur.execute("INSERT INTO product_template (default_code,new_default_code,name) VALUES (%s,%s, %s)",(data_values['default_code'],data_values['new_default_code'],data_values['name']))
					product_template_id = cur.fetchone()[0]
					cur.execute("INSERT INTO product_product (write_uid,product_tmpl_id,name_template,default_code,new_default_code,active,last_default_code) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id", [1,product_template_id,data_values['name'],data_values['default_code'],data_values['new_default_code'],data_values['active'],data_values['last_default_code']])

					#cur.execute("INSERT INTO product_product (default_code,new_default_code,name) VALUES (%s,%s, %s, %s)",(data_values['default_code'],data_values['new_default_code'],data_values['name']))
					conn.commit()




		#posodobi info o produktu, ce nazivi razlicni

		#SLO naziv

		#ce ga ne najde, ga dodaj

		#SLO naziv

		return

	def spare_parts_call_importer(self, cr, uid, ids, context=None):
		spare_parts_config_object = self.pool.get('spare_parts.config.settings')
		config = spare_parts_config_object.browse(cr,uid,1,context)
		
		try:
			global cur
			global conn
			#conn = psycopg2.connect("dbname="config['dbname'] user='yamaha' host='' password='delta#2016'")
			print config
			print config.user
			print config.dbname
			print config.password
			print config.host
			if config.host == False:
				config['host'] = ''
			conn=psycopg2.connect(
			  dbname=config.dbname,
			  user=config.user,
			  host=config.host,
			  password=config.password
			)
			cur = conn.cursor()
		except:
			print "I am unable to connect to server"
			return False
		#filea = '/home/staging/ceniki/general.csv'

		filea = '/home/yamaha/general.csv'
		delim = ';'
		print "filea", filea
		print "delim", delim
		source2 = csv.reader(open(filea,"r"),delimiter=delim)
		row_count = sum(1 for row2 in source2)
		num = 0
		source1 = csv.reader(open(filea,"r"),delimiter=delim)
		data_values = {}

		print "------------------------SPARE PARTS IMPORT-------START-----------------"
		start = time.time()
		for row in source1:

			
			data_values = {}
			default_code = row[0]
			new_default_code = row[1]
			last_default_code = row[2]

			print "default_code: ",default_code
			print str(round(float(num)/float(row_count)*100,2)),"%"
			num += 1

			name = row[3]
			minimum = row[14]
			country = row[8]
			weight = row[9]
			#print "CATEGORY", row[7]
			main_category = row[7][:1]
			mid_category = row[7][1:3]
			small_category = row[7][3:6]
			#print "main_category", main_category
			#print "mid_category", mid_category
			#print "small_category", small_category
			data_values['uom_id'] = 1
			data_values['uom_po_id'] = 1
			data_values['default_code'] = default_code
			data_values['new_default_code'] = new_default_code.strip()
			data_values['last_default_code'] = last_default_code.strip()
			data_values['main_category'] = main_category
			data_values['mid_category'] = mid_category
			data_values['small_category'] = small_category
			data_values['uom_id'] = 1
			data_values['uom_po_id'] = 1
			data_values['default_code'] = default_code.strip()
			data_values['new_default_code'] = new_default_code.strip()
			data_values['name'] = name.strip()
			if data_values['name'] == '' or data_values['name'] == False:
				continue
			data_values['main_category'] = main_category.strip()
			data_values['mid_category'] = mid_category.strip()
			data_values['small_category'] = small_category.strip()
			data_values['active'] = True
			data_values['state'] = ''
			data_values['type'] = 'product'
			data_values['purchase_line_warn'] = 'no-message'
			data_values['sale_line_warn'] = 'no-message'


			if data_values['main_category'] == '2':
				data_values['product_item_type_id'] = 'spare_parts'
				data_values['categ_id'] = 236
			else:
				data_values['product_item_type_id'] = 'accessories'
				data_values['categ_id'] = 237
			data_values['active'] = True
			data_values['state'] = ''
			#YAMAHA
			data_values['product_brand_id'] = 4
			#KG
			data_values['weight_net'] = weight
			if(data_values['new_default_code']) == '999999999900':
				data_values['new_default_code'] = ''
				data_values['state'] = 'end'
			print "data = ", data_values
			
			self.import_spare_parts_db(cr, SUPERUSER_ID, ids, context,data_values)

		end = time.time()
		elapsed = end - start
		print "---Konec ( Cas:", str(round(float(elapsed)/60,2)),"min  ) st. postavk",row_count,"---"
		print "------------------------SPARE PARTS IMPORT-------END-----------------"

