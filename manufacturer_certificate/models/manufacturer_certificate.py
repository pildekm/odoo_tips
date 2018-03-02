# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
import csv


class ManufacturerCertificate(models.Model):
    _name = 'manufacturer.certificate'
    _inherit = ['mail.thread']

    #od attachmenta
    @api.multi
    def _get_attachment_count(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'manufacturer.certificate'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count'])for res in read_group_res)
        for record in self:
            record.attachment_count = attach_data.get(record.id, 0)


    partner_id = fields.Many2one('res.partner', 'Partner')
    first_name = fields.Char('Firstname', size=64, required=True)
    last_name = fields.Char('Lastname', size=64, required=True)
    oib_num = fields.Char('OIB', required=True)
    email = fields.Char('E-mail', size=64, required=True)
    street = fields.Char('Street', size=64, required=True)
    street_number = fields.Char('Street number', size=6, required=True)
    zip = fields.Integer('Poštanski broj', size=5, required=True)
    city = fields.Char('Mjesto', size=64, required=True)
    # country = fields.Many2one('res.country', 'Country', size=64, required=True)
    street_send = fields.Char('Street', size=64)
    street_number_send = fields.Char('Street number', size=64)
    zip_send = fields.Integer('Poštanski broj', size=5)
    city_send = fields.Char('Mjesto', size=64)
    # country_send = fields.Many2one('res.country', 'Country')
    vin_number = fields.Char('VIN', size=64, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                              ('contact', 'Contact'),
                              ('vin', 'VIN'),
                              ('waiting', 'waiting'),
                              ('incorrect', 'Incorrect Documentation'),
                              ('payment', 'Payment'),
                              ('payment_ok', 'Payment ok'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel'), ], default='draft', readonly=True)
    doc1 = fields.Binary('Dokument 1')
    doc2 = fields.Binary('Dokument 2')
    doc3 = fields.Binary('Dokument 3')
    doc4 = fields.Binary('Dokument 4')
    doc5 = fields.Binary('Dokument 5')
    user = fields.Char('Korisnik')
    note = fields.Text('Bilješka')
    vehicle_id = fields.Many2one('manufacturer.certificate.vehicle', 'Vozilo')
    potvrda = fields.Binary('Potvrda proizvođača')
    personal_pickup = fields.Boolean('Preuzimanje u poslovnici')
    attachment_count = fields.Integer(
        compute='_get_attachment_count', string="Number of Attachments")

    @api.multi
    def attachment_tree_view_action(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {
            'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(
            ['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        return action
    #--------------------------------------------attachments----------------------------


    @api.multi
    def name_get(self):
        res = []
        for contact in self:
            name = (contact.id, contact.first_name.capitalize() + ", " + contact.last_name.capitalize())
            res.append(name)
        return res

    def save_contact(self):
        partner_obj = self.env['res.users']
        country_id = self.env['res.country'].search([('name', '=', 'Hrvatska')]).id
        # polja se pune iz frontenda-controlera def certificate_new()
        if not self.personal_pickup:
            # self.street_send = self.street
            # self.street_number_send = self.street_number
            # self.zip_send = self.zip
            # self.city_send = self.city
            self.country_send = country_id
        else:
            self.street_send = False
            self.street_number_send = False
            self.zip_send = False
            self.city_send = False
            self.country_send = False
        self.write({'state': 'contact'})

    @api.onchange('personal_pickup')
    def on_change_personal_pickup(self):
        if self.personal_pickup:
            self.street_send = False
            self.street_number_send = False
            self.zip_send = False
            self.city_send = False
            self.country_send = False
        else:
            country_id = self.env['res.country'].search([('name', '=', 'Hrvatska')]).id
            self.street_send = self.street
            self.street_number_send = self.street_number
            self.zip_send = self.zip
            self.city_send = self.city
            self.country_send = country_id

    def check_vin_number(self):
        self.user = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.name

        #ako možemo a nemamo ga u bazi state = waiting
        #ako možemo state = vin
        #kreiramo vozilo zapišemo ga u model manufacturer.certificate vehicle
        #zapišemo vin  u vin_number na manufacturer.certificate
        self.vin_number = self.vehicle_id.vin.upper()
        # stare vin številke [0:2]
        if len(self.vin_number) == 9:
            vin_tmp = self.vin_number[0:2]
            vin_t = '%' + str(vin_tmp) + '%'
            self.env.cr.execute(""" 
                           select * from manufacturer_certificate_vehicle
                           where vin like %(vin_t)s""", {'vin_t': vin_t})
            res = self.env.cr.dictfetchall()
            for r in res:
                if r['vin'][0:2] == vin_tmp:
                    self.write({'state': 'vin'})
                    print 'Posotji vin'
                    break
        else:
            #za nove vin številke [3:8]
            vin_tmp = self.vin_number[3:8]
            #todo preverjanje vin broja
            # if not vin_tmp[0].isalpha():
            #     raise UserError(_('Nepravilni vin !!!!!.'))
            vin_t = '%' + str(vin_tmp) + '%'
            vin_market = self.vin_number[8:11]
            #provjerimo dali je vozilo za eu tržište
            if vin_market != '000':
                self.vozilo_not_eu()
            else:
                #provjerimo postoji li vozilo u bazi
                self.env.cr.execute(""" 
                                select * from manufacturer_certificate_vehicle
                                where vin like %(vin_t)s""", {'vin_t': vin_t})
                res = self.env.cr.dictfetchall()
                if res:
                    for r in res:
                        if r['vin'][3:8] == vin_tmp and r['vin'][8:11] == '000':
                            self.write({'state': 'vin'})
                            print 'Posotji vin'
                            break

                else:
                    #vozilo ne postoji u bazi
                    self.write({'state': 'waiting'})
                    #adolf provjeri sa yamahom ako nema podatak ide button -> self.centar_za_vozila

    def vozilo_not_eu(self):
        # ako nemožemo izdat certifikat state = cancel
        self.write({'state': 'cancel'})
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_cancel')
        self.env['mail.template'].browse(template.id).send_mail(self.id)


    def centar_za_vozila(self):
        # ako možemo a nemamo ga u bazi state = waiting
        self.write({'state': 'waiting'})
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_waiting')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def provjera_s_tvornicom(self):
        # ako možemo a nemamo ga u bazi state = waiting
        self.write({'state': 'waiting'})
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_company_waiting')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def confirm_documentation(self):
        if self.doc1 or self.doc2 or self.doc3 or self.doc4 or self.doc5:
            self.user = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.name
            self.write({'state': 'waiting'})
            template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_uploaded_doc')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
        else:
            raise UserError(_('Niste priložili nikakvu dokumentaciju. Priložite dokumentaciju i ponovo kliknite "Potvrdi dokumentaciju"'))

    def documentation_ok(self):
        #ove metode upotrebljava samo Adolf
        #če je dokumentacija ok state = payment
            #pošljemo navodila za plačilo v obliki dokumenta
            # create sale order
        so_obj = self.env['sale.order']
        self.user = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.name
        self.write({'state': 'payment'})
        #attachment = self.create_payment_info()
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_doc_od_payment')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    #todo create report for payment info
    def create_payment_info(self):
        #kreiramo dokument z navodili za plačevanje
        #pošljemo mail z navodili i n omogočim download dokumenta
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'manufacturer_certificate.report_payment_data', }

    def payment_ok(self):
        #potrdimo da je plačilo provedeno
        #status = download
        self.user = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.name
        self.write({'state': 'payment_ok'})
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_payment_ok')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_certificate(self):
        #šaljemo potvrdu proizvođača
        self.ensure_one()
        file_name = 'Potvrda proizvodaca' + '.xlsx'
        attachment = {
            'name': 'Potvrda proizvođača ',
            'datas': self.potvrda,
            'datas_fname': file_name,
            'res_model': 'manufacturer.certificate',
            'type': 'binary'
        }
        id_t = self.env['ir.attachment'].create(attachment)
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_send_certificate')
        template.attachment_ids = False
        template.attachment_ids = [(4, id_t.id)]
        self.write({'state': 'done'})
        self.env['mail.template'].browse(template.id).send_mail(self.id)


    def documentation_incorrect(self):
        # če dokumentacija ni ok state = incorrect
            # pošljemo message na mail iz prijave
            # obrišemo dokumente
        self.user = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.name
        self.write({'state': 'incorrect'})
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_incorrect_doc')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.doc1 = None
        self.doc2 = None
        self.doc3 = None
        self.doc4 = None
        self.doc5 = None

    @api.multi
    def send_mail_template(self):
        template = self.env.ref('manufacturer_certificate.manufacturer_certificate_template_first')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        # self.env['mail.template'].search(template.id).send_mail(self.id)

class ManufacturerCertificateVehicle(models.Model):
    _name = "manufacturer.certificate.vehicle"
    #todo vratiti requred fieldove nakon uvoza
    vin = fields.Char('Vin', size=64, required=True)
    model_year = fields.Selection([(num, str(num)) for num in range(1955, (datetime.now().year)+1)], 'Godina modela') #, required=True
    motor_model = fields.Char('Model', size=64, required=True)
    origin = fields.Many2one('res.country', 'Podrijetlo')
    zip = fields.Integer('Poštanski broj', size=5, readonly=True)
    city = fields.Char('Mjesto', size=64, readonly=True)
    certificate_id = fields.One2many('manufacturer.certificate', 'vehicle_id', 'Potvrda proizvođača')
    state = fields.Selection(selection=[('draft', 'Draft'),
                              ('contact', 'Contact'),
                              ('vin', 'VIN'),
                              ('waiting', 'waiting'),
                              ('incorrect', 'Incorrect Documentation'),
                              ('payment', 'Payment'),
                              ('payment_ok', 'Payment ok'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel'), ], related='certificate_id.state', readonly=True, store=True)


    @api.multi
    def name_get(self):
        res = []
        for vehicle in self:
            name = (vehicle.id, str(vehicle.vin.upper()) + ", " + str(vehicle.motor_model.upper()))
            res.append(name)
        return res

    @api.model
    def create(self, vals, cert_id=None):
        # certificate_id = self._context.get('certificate_id', False)
        # if not certificate_id:
        #     certificate_id = cert_id
        # manufacturer_certificate_obj = self.env['manufacturer.certificate'].search([('id', '=', certificate_id)])
        vals['vin'] = vals['vin'].upper()
        vals['motor_model'] = vals['motor_model'].upper()
        # vals['city'] = manufacturer_certificate_obj.city
        # vals['zip'] = manufacturer_certificate_obj.zip
        # vals['certificate_id'] = [(0, 0, certificate_id)]
        vin = vals['vin']
        self.env.cr.execute(""" 
                             select * from manufacturer_certificate_vehicle
                             where vin like %(vin_t)s""", {'vin_t': vin})
        vin_identical = self.env.cr.dictfetchall()
        if vin_identical:
            raise UserError(_('Vozilo sa unesenom Vin oznakom već postoji.'))

        res = super(ManufacturerCertificateVehicle, self).create(vals)
        return res

    def uvezi(self):
        #uvoz csv datoteke
        with open('/home/matija/Desktop/MCV1.csv', 'r') as myfile:
            data = csv.reader(myfile)
            i = 0
            for d in data:
                if i == 0:
                    i += 1
                    pass
                else:
                    country_obj = self.env['res.country'].search([('name', '=', d[3])]).id
                    if not country_obj:
                        country_obj = None
                    self.env.cr.execute("""
                                 insert into manufacturer_certificate_vehicle (origin, city, model_year, zip, vin, motor_model, state)
                                 values (%(origin)s, %(city)s, %(model_year)s, %(zip)s, %(vin)s, %(motor_model)s, %(state)s )""", {'origin': country_obj, 'city': d[5] or None,
                                                                                                                        'model_year': d[2] or None, 'zip': d[4] or None,
                                                                                                                        'vin': d[0] or None, 'motor_model': d[1] or None,
                                                                                                                        'state': 'done', })
