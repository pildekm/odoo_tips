# -*- coding: utf-8 -*-
# Part of GMM company limited

from datetime import datetime
from odoo import api, fields, models, _



class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def get_invoice_data(self):
        for move in self:
            if move.sale_line_id:
                move.invoice_number = move.sale_line_id.invoice_lines.invoice_id.number + '-' + str(move.sale_line_id.invoice_lines.invoice_line_sequence)
                move.amount = move.sale_line_id.invoice_lines.price_subtotal
                move.invoice_date = move.sale_line_id.invoice_lines.invoice_id.date_invoice


    #TODO: field names n english and .po file in slovenian

    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    invoice_date = fields.Date('Datum racuna', compute=get_invoice_data, readonly=True)
    amount = fields.Monetary('Znesek', currency_field='company_currency_id', compute=get_invoice_data, readonly=True)
    invoice_number = fields.Char('Broj racuna', compute=get_invoice_data, readonly=True)
    date_out = fields.Datetime('Datum otpreme', related='picking_id.date_done', readonly=True)
