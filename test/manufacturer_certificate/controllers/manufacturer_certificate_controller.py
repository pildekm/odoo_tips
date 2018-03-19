# -*- coding: utf-8 -*-
import odoo
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception
from odoo.exceptions import AccessError
from odoo.exceptions import UserError
from datetime import datetime
from odoo.models import check_method_name
from odoo.tools.translate import _
import base64
import json
from odoo import SUPERUSER_ID
from odoo import http, _


class CertificateRegister(http.Controller):

    del_att_id = 0

    #otvaramo login page ako partner nema potpune podatke
    #ako več postoji partner otvaramo mu popis zahtjeva
    @http.route('/manufacturer/certificate', type='http', auth="user", website=True)
    def certificate_signup(self, redirect=None, **kw):
        # ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        # if not request.uid:
        #     request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        uid = http.request.env.context.get('uid')
        partner_id = http.request.env['res.users'].search([('id', '=', uid)]).partner_id.id
        partner_obj = http.request.env['res.partner'].search([('id', '=', partner_id)])

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form
            partner_vals = {'vat': form_data['oib_num'],
                            'street': form_data['street'],
                            'street2': form_data['street_number'],
                            'zip': form_data['zip'],
                            'city': form_data['city'], }
            partner_obj.write(partner_vals)


            if uid is not False:
                request.params['login_success'] = True
                if not redirect:
                    redirect = '/web'
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            manufacturer_certificate_obj = http.request.env['manufacturer.certificate']

        #ako nema podataka otvara se forma za unos
        if not partner_obj.vat or not partner_obj.street or not partner_obj.street2 or not partner_obj.zip or not partner_obj.city:
            return request.render('manufacturer_certificate.certificate', values)
        else:
            #izrendaj stranicu sa svim zahtjevima za izdavanje potvrde usera
            http.request.env.cr.execute("""select mc.first_name ,
                                                  mc.last_name ,
                                                  mc.vin_number,
                                                  mc.state,
                                                  mcv.motor_model as vehicle_id
                                            FROM manufacturer_certificate mc
                                            LEFT JOIN manufacturer_certificate_vehicle mcv on mc.vehicle_id = mcv.id
                                            where mc.partner_id = %(partner_id)s""", {'partner_id': partner_id})
            values['certificates'] = http.request.env.cr.dictfetchall()
            return request.render('manufacturer_certificate.user_certificate_tree_view', values)
            # self.create_mc_obj(partner_obj)


    @http.route('/manufacturer/certificate_send_address', type='http', auth="user", website=True)
    def certificate_send_address(self, redirect=None, **kw):
        # ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        uid = http.request.env.context.get('uid')
        partner_id = http.request.env['res.users'].search([('id', '=', uid)]).partner_id.id
        partner_obj = http.request.env['res.partner'].search([('id', '=', partner_id)])
        values['send_address'] = {'city': partner_obj.city,
                                  'zip': partner_obj.zip,
                                  'street': partner_obj.street,
                                  'street_number': partner_obj.street2, }

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form

            return request.render('manufacturer_certificate.certificate_send_address', values)


    @http.route('/manufacturer/certificate_new', type='http', auth="user", website=True)
    def certificate_new(self, redirect=None, **kw):
        # ensure_db()
        context = request.context.copy()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        uid = http.request.env.context.get('uid')
        partner_id = http.request.env['res.users'].search([('id', '=', uid)]).partner_id.id
        partner_obj = http.request.env['res.partner'].search([('id', '=', partner_id)])

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form
            new_mc_obj_id = self.create_mc_obj(partner_obj, form_data)
            context.update({'mc_id': new_mc_obj_id})
            country_ids = http.request.env['res.country'].search([])
            values['countrys'] = [country_id for country_id in country_ids]
            values['years'] = [num for num in range(1955, ( datetime.now().year) + 1)]
            values['mc_id'] = new_mc_obj_id
            return request.render('manufacturer_certificate.user_new_certificate', values)

    # prvi korak kreiramo Manufacturer certificate
    def create_mc_obj(self, partner, form_data):
        if form_data.get('personal_pickup', False):
            personal_pickup = True
        else:
            personal_pickup = False
        partner_name = partner.name.split()
        vals = {'partner_id': partner.id,
                'first_name': partner_name[0],
                'last_name': partner_name[1],
                'oib_num': partner.vat,
                'street': partner.street,
                'street_number': partner.street2,
                'zip': partner.zip,
                'city': partner.city,
                'email': partner.email,
                'street_send': form_data['street_send'],
                'street_number_send': form_data['street_number'],
                'zip_send': form_data['zip_send'],
                'city_send': form_data['city_send'],
                'personal_pickup': personal_pickup, }
        manufacturer_certificate_obj = http.request.env['manufacturer.certificate']
        new_manufacturer_certificate = manufacturer_certificate_obj.create(vals)
        new_manufacturer_certificate.save_contact()
        return new_manufacturer_certificate.id


    @http.route('/manufacturer/certificate_create', type='http', auth="user", website=True)
    def certificate_create(self, redirect=None, **kw):
        # ensure_db()
        context = request.context
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        uid = http.request.env.context.get('uid')

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form
            new_mcv_obj_id = self.create_mcv_obj(form_data)
            manufacturer_ceretificate_obj = http.request.env['manufacturer.certificate'].search([('id', '=', form_data['MC_id'])])
            manufacturer_ceretificate_obj.write({'vehicle_id': new_mcv_obj_id, })
            message = manufacturer_ceretificate_obj.check_vin_number()
            values['MC_id'] = form_data['MC_id']
            values['vin'] = form_data['vin']
            values['motor_model'] = form_data['motor_model']
            values['model_year'] = form_data['model_year']
            values['origin'] = form_data['origin']
            #todo rendaj zadnjo stran i dodavanje dokumentacije
            if message == 'cancel':
                return request.render('manufacturer_certificate.certificate_message_cancel', values)
            else:
                return request.render('manufacturer_certificate.upload_documents', values)


    #kreiramo vozilo
    def create_mcv_obj(self, form_data):
        manufacturer_ceretificate_obj = http.request.env['manufacturer.certificate'].search([('id', '=', form_data['MC_id'])])
        country_id = http.request.env['res.country'].search([('name', '=', form_data['origin'])]).id
        vals = {'vin': form_data['vin'],
                'motor_model': form_data['motor_model'],
                'model_year': int(form_data['model_year']),
                'origin': country_id,
                'zip': manufacturer_ceretificate_obj.zip,
                'city': manufacturer_ceretificate_obj.city, }
                #'certificate_id': [(0, 0, int(form_data['MC_id']))], }
        manufacturer_certificate_vehicle_obj = http.request.env['manufacturer.certificate.vehicle']
        new_manufacturer_certificate_vehicle_obj = manufacturer_certificate_vehicle_obj.create(vals, int(form_data['MC_id']))
        mcv_id = new_manufacturer_certificate_vehicle_obj.id
        # val = [(1, mcv_id, {'certificate_id': int(form_data['MC_id'])})]
        # new_manufacturer_certificate_vehicle_obj.write(val)
        return mcv_id



    @http.route('/manufacturer/certificate_final', type='http', auth="user", website=True)
    def certificate_final(self, redirect=None, **kw):
        # ensure_db()
        context = request.context
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        uid = http.request.env.context.get('uid')

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form
            manufacturer_ceretificate_obj = http.request.env['manufacturer.certificate'].search([('id', '=', form_data['MC_id'])])
            manufacturer_ceretificate_obj.confirm_documentation(form_data['MC_id'])
            #opet izrendaj isti template ako nema dokumentacije
            return request.render('manufacturer_certificate.certificate_message_vin', values)


    #--Multiple Attachments--------------------------------------------------------------------------------------------

    @http.route('/manufacturer/certificate_upload_documents', type='http', auth="user",  method='POST', website=True)
    def certificate_file_upload(self, attachment_id=False, **post):
        global del_att_id
        if post.get('Upload-File'):
            data = {
                'attachments': []
            }
            orphan_attachment_ids = []
            for field_name, field_value in post.items():
                if hasattr(field_value, 'filename'):
                    field_name = field_name.rsplit('[', 1)[0]
                    field_value.field_name = field_name
                    data['attachments'].append(field_value)

            form_data = request.httprequest.form
            if form_data:
                for file in data['attachments']:

                    custom_field = None
                    attachment_value = {
                        'name': file.field_name if custom_field else file.filename,
                        'datas': base64.encodestring(file.read()),
                        'datas_fname': file.filename,
                        'res_model': 'manufacturer.certificate',
                        'res_id': int(form_data['MC_id']),
                    }

                    attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)

        values = {}

        att_obj = http.request.env['ir.attachment'].search([('res_id', '=', int(form_data['MC_id'])), ('res_model', '=', 'manufacturer.certificate')])
        # globalna varijabla
        if self.del_att_id != 0:
            att_for_del = http.request.env['ir.attachment'].search([('res_id', '=', int(form_data['MC_id'])),
                                                                    ('res_model', '=', 'manufacturer.certificate'),
                                                                    ('id', '=', self.del_att_id)])

            objects_all = att_obj - att_for_del
            values['attachment_objs'] = objects_all - attachment_id
            attachment_id.sudo().unlink()
            att_for_del.sudo().unlink()
            self.del_att_id = 0
        else:
            values['attachment_objs'] = att_obj

        manufacturer_certificate_obj = http.request.env['manufacturer.certificate'].search([('id', '=', int(form_data['MC_id']))])
        values['attachment_count'] = manufacturer_certificate_obj.attachment_count
        values['MC_id'] = form_data['MC_id']
        values['vin'] = form_data['vin']
        values['motor_model'] = form_data['motor_model']
        values['model_year'] = form_data['model_year']
        values['origin'] = form_data['origin']
        return request.render('manufacturer_certificate.upload_documents', values)


    @http.route('/certificate/remove_upload', type='json', auth="public", website=True)
    def remove_file_upload(self, attachment_id, mc_id):
        global del_att_id
        context = request.context
        context = context.copy()
        if attachment_id:
            attachment_obj = request.env['ir.attachment'].search([('id', '=', attachment_id)])
            context.update({'attachment_id': attachment_id})
            if attachment_obj:
                # attachment_obj.sudo().unlink()
                self.del_att_id = attachment_id
                # http.request.env.cr.execute("""delete from ir_attachment where id = %(attachment_id)s""",
                #                             {'attachment_id': attachment_id})
                # self.certificate_file_upload_test(attachment_id)
        return True



    # @http.route('/manufacturer/certificate_upload_documents_test', type='http', auth="user", website=True)
    # def certificate_file_upload_test(self, del_attachment=False, **post):
    #     if post.get('Upload-File'):
    #         data = {
    #             'attachments': []
    #         }
    #         orphan_attachment_ids = []
    #         for field_name, field_value in post.items():
    #             if hasattr(field_value, 'filename'):
    #                 field_name = field_name.rsplit('[', 1)[0]
    #                 field_value.field_name = field_name
    #                 data['attachments'].append(field_value)
    #
    #         form_data = request.httprequest.form
    #         if form_data:
    #             for file in data['attachments']:
    #
    #                 custom_field = None
    #                 attachment_value = {
    #                     'name': file.field_name if custom_field else file.filename,
    #                     'datas': base64.encodestring(file.read()),
    #                     'datas_fname': file.filename,
    #                     'res_model': 'manufacturer.certificate',
    #                     'res_id': 157,  # int(form_data['MC_id']),
    #                 }
    #                 attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
    #                 orphan_attachment_ids.append(attachment_id.id)
    #                 if orphan_attachment_ids:
    #                     values = {
    #                         'body': _('<p>Attached files : </p>'),
    #                         'model': 'manufacturer.certificate',
    #                         'message_type': 'comment',
    #                         'no_auto_thread': False,
    #                         'res_id': 157,  # int(form_data['MC_id']),
    #                         'attachment_ids': [(6, 0, orphan_attachment_ids)],
    #                     }
    #                     # mail_id = request.env['mail.message'].sudo().create(values)
    #     values = {}
    #     att_obj = http.request.env['ir.attachment'].search(
    #         [('res_id', '=', 157), ('res_model', '=', 'manufacturer.certificate')])
    #     # if del_attachment:
    #     #     att_for_del = http.request.env['ir.attachment'].search([('res_id', '=', 157),
    #     #                                                             ('res_model', '=', 'manufacturer.certificate'),
    #     #                                                             ('id', '=', del_attachment)])
    #     #
    #     #     if att_for_del:
    #     #         values['attachment_objs'] = att_obj - att_for_del
    #     # else:
    #     values['attachment_objs'] = att_obj
    #     manufacturer_certificate_obj = http.request.env['manufacturer.certificate'].search([('id', '=', 157)])
    #
    #     values['attachment_count'] = manufacturer_certificate_obj.attachment_count
    #     values['MC_id'] = 157
    #     values['vin'] = '456000000000000000000'
    #     values['motor_model'] = 'der'
    #     values['model_year'] = '1978'
    #     values['origin'] = 'Hrvatska'
    #     return request.render('manufacturer_certificate.upload_documents_test', values)





