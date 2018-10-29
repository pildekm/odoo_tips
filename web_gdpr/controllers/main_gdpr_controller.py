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
from odoo.addons.auth_signup.controllers.main import AuthSignupHome



class WebGdpr(http.Controller):

    @http.route('/gdpr/data', type='http', auth="user", website=True)
    def gdpr_data_create(self, **kwargs):
        uid = http.request.env.context.get('uid')
        partner_id = http.request.env['res.users'].search([('id', '=', uid)]).partner_id

        return http.request.env['report.web_gdpr.report_get_my_data'].sudo().render_html([partner_id.id])



    @http.route('/gdpr/delete', type='http', auth="user", website=True)
    def gdpr_data_delete_modal(self, **kwargs):
        uid = http.request.env.context.get('uid')
        user_id = http.request.env['res.users'].search([('id', '=', uid)])
        partner_id = user_id.partner_id

        values = {'street': 'GDPR_ulica',
                  'city': 'GDPR_grad',
                  'zip': 'GDPR_zip',
                  'email': 'GDPR_email',
                  'phone': 'GDPR_phone',
                  'vat': 'GDPR_vat',
                  'partner_name_send': 'GDPR_name',
                  'email_send': 'GDPR_email',
                  'street_send': 'GDPR_street',
                  'zip_send': 'GDPR_zip',
                  'city_send': 'GDPR_city',}

        partner_id.sudo().write(values)
        user_id.sudo().unlink()
        print '------------------------User je obrisan----------------------------------'

        # return request.render('web_gdpr.details_inherit', values)

    @http.route('/gdpr/gdpr_data', type='http', auth="public", website=True)
    def gdpr_data_info(self, **kwargs):
       values = {}
       return request.render('web_gdpr.gdpr_data_info', values)


    @http.route('/gdpr/legal_data', type='http', auth="public", website=True)
    def gdpr_data_legal(self, **kwargs):
        values = {}
        return request.render('web_gdpr.gdpr_legal', values)

    @http.route('/gdpr/privacy_policy', type='http', auth="public", website=True)
    def gdpr_data_privacy(self, **kwargs):
        values = {}
        return request.render('web_gdpr.gdpr_privacy_policy', values)



class AuthSignupHomeGDPR(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        uid = http.request.env.context.get('uid')
        user_id = http.request.env['res.users'].search([('id', '=', uid)])
        partner_id = user_id.partner_id

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            form_data = request.httprequest.form
            if not form_data['rules']:
                qcontext["error"] = _("Polje označeno * je obavezno polje ako se želite registriati.")
                return request.render('auth_signup.signup', qcontext)
            else:
                qcontext['rules'] = True

        return super(AuthSignupHomeGDPR, self).web_auth_signup(*args, **kw)

    def _signup_with_values(self, token, values):
        values_gdpr = {'rules': True}
        values.update(values_gdpr)
        return super(AuthSignupHomeGDPR, self)._signup_with_values(token, values)




