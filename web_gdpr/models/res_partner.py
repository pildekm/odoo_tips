# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # usluge = fields.Boolean('Usluge', readonly=True, help='Podsjetnici za TM Zagreb usluge, npr. Servis')
    # ponude = fields.Boolean('Ponude', readonly=True, help='Nove relevantne ponude za vas i vaše vozilo.')
    # response = fields.Boolean('Promocija', readonly=True, help='Prikupljanje vaših stavova o proizvodima i uslugama tvrtke TM Zagreb.')
    # invite = fields.Boolean('Pozivnice', readonly=True, help='Pozivnice na TM Zagreb događaje.')
    rules = fields.Boolean('Privola', readonly=True, help='Molimo Vas da ažurirate svoje osobne podatke te da prihvatite da ste ovu obavijest pročitali i razumjeli i da prihvatom dajete privolu za obradu Vaših osobnih podataka.')

    # @api.model
    # def create(self, vals):
    #     int=5
    #
    #     return super(ResPartner, self).create(vals)