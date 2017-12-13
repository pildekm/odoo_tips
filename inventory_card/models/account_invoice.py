# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('sequence')
    @api.multi
    def compute_seq(self):
	    seq = 1
	    for line in self:
		    line.invoice_line_sequence = seq
		    seq += 1

    invoice_line_sequence = fields.Integer(compute=compute_seq, help="Gives the sequence of this line when displaying the invoice.")