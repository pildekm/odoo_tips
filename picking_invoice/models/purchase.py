from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	# TODO: Popravljen modul
	def create_file_for_yamaha(self):
		ir_model_data = self.env['ir.model.data']
		spare_purchase_order_dir = self.env['ir.config_parameter'].sudo().get_param(
			'spare_parts_config_settings.spare_purchase_order_dir')
		brand_id_yamaha = ir_model_data.get_object_reference('product_brand', 'yamaha')[1]
		brand_id_ixs = ir_model_data.get_object_reference('product_brand', 'ixs')[1]
		narocilo = self.name[-5:]
		narocilo_accessories = ("1" + narocilo[-4:])
		for order in self:
			for line in order.order_line:
				if line.product_id.product_brand_id.id == brand_id_yamaha:
					if line.product_id.product_item_type_id == 'accessories':
						datoteka = spare_purchase_order_dir+'A' + narocilo + '.ORD'

						#datoteka = '/home/staging/a-shipment/A' + narocilo + '.ORD'

						file = open(datoteka, 'a')
						print line
						print self.id

						line_readline = '5050' + '\t' + line.product_id.default_code.replace('-', '') + '\t' + str(
							int(line.product_qty)) + '\t' + line.product_id.name.replace('-',
						                                                                 '') + '\t\t\t\t' + '1' + '\t\t' + str(
							narocilo_accessories) + '\t\t\n'

						file.write(line_readline)
						file.close()
					if line.product_id.product_item_type_id == 'spare_parts':
						# datoteka = '/home/staging/a-shipment/P' + narocilo + '.ORD'
						datoteka = a_shipment_dir + 'P' + narocilo + '.ORD'
						file = open(datoteka, 'a')
						#line_readline = '5050'+'\t'+line.name.replace('-', '').replace('[', '').replace(']', '')[:12]+'\t'+str(int(line.product_qty))+'\t'+ line.name.replace('-','').replace(']', '')[13:]+'\t'+'1'+'\t'+str(narocilo)+'\n'

						line_readline = '5050' + '\t' + line.product_id.default_code.replace('-', '')+'\t'+str(int(line.product_qty))+'\t'+ line.product_id.name.replace('-', '')+'\t\t\t\t'+'1'+'\t\t' + str(narocilo)+'\t\t\n'

						file.write(line_readline)
						file.close()


				else:

					raise UserError(_("Not Yamaha"))
					#print "ni Yamaha"


	@api.multi
	def button_approve(self, force=False):
		for order_line in self.order_line:
			if not order_line.ref_number:
				raise UserError(_("You must insert Supplier ref for all parts"))
		self.write({'state': 'purchase'})
		self._create_picking()
		if self.company_id.po_lock == 'lock':
			self.write({'state': 'done'})

		#self

		#raise UserError(_("You must insert Supplier ref"))



		return {}

	@api.multi
	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent']:
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step' \
					or (order.company_id.po_double_validation == 'two_step' \
							    and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id)):
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
				self.create_file_for_yamaha()
		return True