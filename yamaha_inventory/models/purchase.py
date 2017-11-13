# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	parts_ref = fields.Integer('Part ref', size=4)
	accessories_ref = fields.Integer('Accessories ref', size=5)
	ixs_ref = fields.Integer('IXS ref')

	_sql_constraints = [(
		'parts_ref_unique',
		'unique(parts_ref)',
		'Parts ref already exists!'
	)]

	@api.one
	@api.constrains('parts_ref')
	def _check_unique_parts_ref(self):

		if self.parts_ref :
			same_parts_ref = self.search([('parts_ref', '=', self.parts_ref),('id', '!=', self.id)])
			if same_parts_ref:
				raise ValidationError(_("Parts ref already exists '%s' in ids = '%s'.") % (self.parts_ref,same_parts_ref))
PurchaseOrder()

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	@api.one
	@api.depends('order_id.parts_ref', 'order_id.accessories_ref','order_id.ixs_ref')
	def get_ref(self):
		purchase_order = self.env['purchase.order']
		ref = {'spare_parts': self.parts_rel, 'accessories': self.accessories_rel, 'ixs': self.ixs_rel}
		for p in self:
			product_id = p.product_id.id
			product_item_type_id = p.product_id.product_item_type_id
			#na temelju rezultata iznad napravi provjeru i zapiši ref broj u line

			if product_item_type_id == 'spare_parts':
				p.ref_number = ref['spare_parts']
			if product_item_type_id == 'accessories':
				p.ref_number = ref['accessories']
			if product_item_type_id == 'ixs':
				p.ref_number = ref['ixs']

	ref_number = fields.Integer('Reference number', compute='get_ref', default=False,store=True)
	accessories_rel = fields.Integer('Accessories', related='order_id.accessories_ref')
	parts_rel = fields.Integer('Part', related='order_id.parts_ref')
	ixs_rel = fields.Integer('IXS', related='order_id.ixs_ref')

