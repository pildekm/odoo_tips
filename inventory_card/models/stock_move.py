# -*- coding: utf-8 -*-
# Part of GMM company limited

from datetime import datetime
from odoo import api, fields, models, _



class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def get_invoice_data(self):
        for move in self:
            if move.sale_line_id.invoice_lines.invoice_id.number:
                print move.sale_line_id.invoice_lines.invoice_id.number
                print (str(move.sale_line_id.invoice_lines.invoice_line_sequence))
                move.invoice_number = move.sale_line_id.invoice_lines.invoice_id.number + '-' + str(move.sale_line_id.invoice_lines.invoice_line_sequence)
                move.invoice_date = move.sale_line_id.invoice_lines.invoice_id.date_invoice
            move.amount_out = move.sale_line_id.invoice_lines.price_subtotal
            move.partner_ic = move.sale_line_id.invoice_lines.invoice_id.partner_id.id
            if move.purchase_line_id:
                move.amount_in = move.purchase_line_id.price_subtotal
                #move.amount_in = move.purchase_line_id.price_total
                #move.amount_in = move.purchase_line_id.price_unit


    #TODO: field names n english and .po file in slovenian

    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    invoice_date = fields.Date('Datum racuna', compute=get_invoice_data, readonly=True)
    amount_out = fields.Monetary('Znesek izlaz', currency_field='company_currency_id', compute=get_invoice_data, readonly=True)
    invoice_number = fields.Char('Broj racuna', compute=get_invoice_data, readonly=True)
    date_out = fields.Datetime('Datum otpreme', related='picking_id.date_done', readonly=True)
    amount_in = fields.Monetary('Znesek ulaz',  compute=get_invoice_data, currency_field='company_currency_id', readonly=True)
    partner_ic = fields.Many2one('res.partner', string='Prejemnik', compute=get_invoice_data, readonly=True)
