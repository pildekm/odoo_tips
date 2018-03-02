# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import base64
from odoo.exceptions import UserError

class UploadCertificationDocument(models.TransientModel):
    _name = 'upload.certification.document'
    _description = 'Wizard for certification documents upload'

    data1 = fields.Binary('Dokument 1')
    data2 = fields.Binary('Dokument 2')
    data3 = fields.Binary('Dokument 3')
    data4 = fields.Binary('Dokument 4')
    data5 = fields.Binary('Dokument 5')
    name = fields.Char(string='Filename Name')
    delimeter = fields.Char('Delimeter', default='\t', help='Default delimeter is ","')


    @api.multi
    def save_documents(self):
        mc_obj = self.env['manufacturer.certificate'].search([('id', '=', self._context['active_id'])])
        # data = base64.b64decode(self.data1)
        if not mc_obj.doc1:
            mc_obj.doc1 = self.data1
        if not mc_obj.doc2:
            mc_obj.doc2 = self.data2
        if not mc_obj.doc3:
            mc_obj.doc3 = self.data3
        if not mc_obj.doc4:
            mc_obj.doc4 = self.data4
        if not mc_obj.doc5:
            mc_obj.doc5 = self.data5


