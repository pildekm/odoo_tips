# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class pos_config(models.Model):
    _inherit = "pos.config"

    pos_auto_invoice = fields.Boolean('POS auto invoice', help='POS auto to checked to invoice button', default=1)
    pos_auto_customer_guest = fields.Boolean('Auto select Guest as customer', default=1)
    pos_auto_customer_guest_id = fields.Integer(string='Id of Guest Customer')
    pos_auto_payment_cash = fields.Boolean('Auto select Cash as payment', default=1)
    pos_auto_payment_cash_id = fields.Integer(string='ID of Cash Payment')
    receipt_invoice_number = fields.Boolean('Receipt show invoice number', default=1)
    receipt_customer_vat = fields.Boolean('Receipt show customer VAT', default=1)
    receipt_zoi = fields.Boolean('Receipt show ZOI', default=1)
    receipt_eor = fields.Boolean('Receipt show EOR', default=1)
    receipt_fiscal_number = fields.Boolean('Receipt show Fiscal number', default=1)
    receipt_qrcode = fields.Boolean('Receipt show QRcode', default=1)
    receipt_company_logo = fields.Boolean('Show company logo', default=1)
