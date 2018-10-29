# -*- coding: utf-8 -*-
from odoo import api, models


class GdprMyData(models.AbstractModel):
    _name = 'report.web_gdpr.report_get_my_data'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('web_gdpr.report_get_my_data')
        data = self.env['res.partner'].search([('id', '=', docids[0])])

        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': data, }

        return self.env['report'].render('web_gdpr.report_get_my_data', docargs)