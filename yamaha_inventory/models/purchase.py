# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	parts_ref = fields.Integer('Part ref', size=4)
	accessories_ref = fields.Integer('Accessories ref', size=5)
	ixs_ref = fields.Integer('IXS ref')

	@api.one
	def write(self, vals, context=None):
		ref = {'spare_parts': vals.get('parts_ref', ''),
		       'accessories': vals.get('accessories_ref',''),
		       'ixs': vals.get('ixs_ref', '')}
		res={}
		pol = self.env['purchase.order.line'].search([('order_id', '=', self.id),])
		pol_ids = pol._ids
		self.env.cr.execute("""
			select pol.id, pt.product_item_type_id from purchase_order_line pol
			left join product_product pp on pol.product_id = pp.id
			left join product_template pt on pt.id = pp.product_tmpl_id 
			where pol.id in %(pol_ids)s""", {'pol_ids': pol_ids})
		for r in self.env.cr.dictfetchall():
			res[r['id']] = r['product_item_type_id']
		#update one2many
		vals1 = [(1, id, {'ref_number': ref[res[id]]}) for id in pol_ids]
		vals.update({'order_line': vals1})
		return super(PurchaseOrder, self).write(vals)


class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	# @api.one
	# def get_ref(self):
	# 	purchase_order = self.env['purchase.order']
	# 	ref = {'spare_parts': self.parts_rel, 'accessories': self.accessories_rel, 'ixs': self.ixs_rel}
	# 	for p in self:
	# 		product_id = p.product_id.id
	# 		product_item_type_id = p.product_id.product_item_type_id
	# 		#na temelju rezultata iznad napravi provjeru i zapiši ref broj u line
	#
	# 		if product_item_type_id == 'spare_parts':
	# 			p.update({'ref_number': ref['spare_parts']})
	# 		if product_item_type_id == 'accessories':
	# 			p.update({'ref_number': ref['accessories']})
	# 		if product_item_type_id == 'ixs':
	# 			p.update({'ref_number': ref['ixs']})

	ref_number = fields.Integer('Reference number')
	#ref_number = fields.Integer('Reference number', compute='get_ref')
	# accessories_rel = fields.Integer('Accessories', related='order_id.accessories_ref')
	# parts_rel = fields.Integer('Part', related='order_id.parts_ref')
	# ixs_rel = fields.Integer('IXS', related='order_id.ixs_ref')
	# reference = fields.Integer('Reference', related='ref_number', store=True, default=False)
