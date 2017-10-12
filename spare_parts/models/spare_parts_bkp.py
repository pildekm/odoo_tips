## Imports
from StringIO import StringIO
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools.translate import _
import base64
import csv
import logging
import re
import openerp.addons.decimal_precision as dp
## Get the logger:
## Declare a temporary container:

class ProductVariantModelNewDefaultCode(osv.osv):
    _inherit = 'product.product'
    def list_default_code_change(self, new_default_code ,all_products,cr,uid,context):

        if new_default_code:
            element = self.search(cr, uid, ['|',('active', '=', False),('active', '=', True),("default_code", "=",  new_default_code)],  context=context)
            #all_products += element[0]
            if element:
                #all_products.append(element[0])
                all_products.insert(0,element[0])
                if not new_default_code:
                    return all_products
                product_info = self.read(cr, uid, element[0], ["default_code","new_default_code"], context=context)
                if product_info['new_default_code']:
                    if product_info['default_code'] == product_info['new_default_code']:
                        return
           
                    next_element = self.list_default_code_change(product_info['new_default_code'],all_products,cr,uid,context)
                else:
                    return all_products
        return all_products
    #FIND FIRST ELEMENT ELEMENT AND APPEND IT
    def find_first(self, default_code ,all_products,cr,uid,context):
        product_old_cat = self.search(cr, uid, ['|',('active', '=', False),('active', '=', True),("new_default_code", "=",  default_code)],  context=context)

        if not product_old_cat:

            product_old_cat = self.search(cr, uid, ['|',('active', '=', False),('active', '=', True),("default_code", "=",  default_code)],  context=context)
            product_info = self.read(cr, uid, product_old_cat[0], ["default_code","new_default_code"], context=context)
 

            all_products.insert(0,product_old_cat[0])
            if product_info['default_code'] == product_info['new_default_code']:
                return
            if product_info['new_default_code']:
                first_element = self.list_default_code_change(product_info['new_default_code'],all_products,cr,uid,context)

        else:
            product_info = self.read(cr, uid, product_old_cat[0], ["default_code","new_default_code"], context=context)

            #RECURSIVE
            if product_info['default_code'] == product_info['new_default_code']:
                return
            first_element = self.find_first(product_info['default_code'],all_products,cr,uid,context)
        return 
    def get_related_default_code(self, cr, uid, ids, field_names=None, arg=None, context=None):
        """
        Returns all related product:
        """
        ## Copy the context:
        context = context.copy()
        
        ## Declare the return value:
        result = {}

        ## If no IDs supplied, just return as is:
        if not ids:
            return result
  
        for id in ids:
            all_products = []
            #Zgodovina sprememb kataloskih
            product_info = self.read(cr, uid, id, ["default_code","new_default_code"], context=context)
      
            if product_info['default_code'] == product_info['new_default_code']:
                result[id] = list(set([]))
            related_default_code_list = self.find_first(product_info['default_code'],all_products,cr,uid,context)

            #result[id] = all_products
            if len(all_products) > 1:
                result[id] = all_products
            else:
                result[id] = []
        ## Done, return with a smiley face:
        return result
    default_code =  fields.Char('Last Internal Reference', select=True)
    new_default_code = fields.Char('New Internal Reference', select=True)
    related_default_code = fields.function(get_related_default_code, type="one2many", relation="product.product", string="Related Default Code")

    _columns = {
        'last_default_code' : fields.char('Last Internal Reference', select=True),
        'new_default_code' : fields.char('New Internal Reference', select=True),
        'related_default_code': fields.function(get_related_default_code, type="one2many", relation="product.product", string="Related Default Code"),
    }
ProductVariantModelNewDefaultCode()

class product_template(osv.osv):
	_name = "product.template"
	_inherit = "product.template"

	
	_columns = {
		'product_item_type_id': fields.selection([
		('spare_parts','Spare Parts'),
		('accessories','Accessories'),
		('motor','Motor')], 'Item type', help='Select a item type.', require=True),
		'web_product': fields.boolean('Web Product', help="By unchecking the Web Product field you can disable a website product treatment."),


	}
