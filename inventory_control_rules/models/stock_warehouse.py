# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    def _set_date_today(self):
	    date = fields.Date.from_string(fields.Date.today())
	    #print('Evo mene moji ljudi')
	    return date.strftime('%Y') + '-' + date.strftime('%m') + '-' + date.strftime('%d')

    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    date_today = fields.Date(string='Date today', default=_set_date_today, readonly=True)
    #season = fields.Boolean('Is season', compute='is_season', readonly=True)
    season_min_qty = fields.Integer('Minimum quantity in season')
    non_season_min_qty = fields.Integer('Minimum quantity in non season')


    @api.onchange('season_min_qty', 'date_start', 'date_end', 'date_today')
    def set_season_min_qty(self):
        if self.date_start <= self.date_today <= self.date_end and self.season_min_qty:
            self.product_min_qty = self.season_min_qty
        elif self.date_start > self.date_today and self.non_season_min_qty:
            self.product_min_qty = self.non_season_min_qty
        else:
            print('daytum is so wrong')
