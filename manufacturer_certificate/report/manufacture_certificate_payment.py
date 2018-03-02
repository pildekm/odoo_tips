# -*- coding: utf-8 -*-

from odoo import api, models

class ManufacturerCertificatePayment(models.AbstractModel):
    _name = 'report.manufacturer_certificate.report_payment_data'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('manufacturer_certificate.report_payment_data')
        data = self.env['manufacturer.certificate'].search([('id', '=', docids[0])])
        datas = {'first_name': data.first_name,
               'last_name': data.last_name,
                'street': data.street,
                'street_number': data.street_number,
                'zip': data.zip,
                'city': data.city,
               }
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': data,
            'data': datas, }
        # return report_obj.render('manufacturer_certificate.report_payment_data', docargs)
        print datas
        return self.env['report'].render('manufacturer_certificate.report_payment_data', docargs)