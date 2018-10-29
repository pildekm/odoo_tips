# -*- coding: utf-8 -*
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController
from odoo import api, http, SUPERUSER_ID
from odoo.addons.web.controllers.main import ensure_db, Home, Session, WebClient
from odoo.addons.point_of_sale.controllers.main import PosController
from odoo.addons.base.ir.ir_qweb import AssetsBundle
import json
import logging
import base64
import werkzeug.utils
import time
from werkzeug import exceptions, url_decode
from werkzeug.datastructures import Headers
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from odoo.http import Controller, route, request
from odoo.tools import html_escape
from odoo.addons.web.controllers.main import _serialize_exception, content_disposition
from odoo.tools.safe_eval import safe_eval

class PosController(PosController):
    @route(['/pos/web/report/barcode', '/pos/web/report/barcode/<type>/<path:value>'],  type='http', auth='user')
    def pos_barcode(self, type, value, width=600, height=100, humanreadable=0):
        """Contoller able to render barcode images thanks to reportlab.
        Samples:
            <img t-att-src="'/report/barcode/QR/%s' % o.name"/>
            <img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' %
                ('QR', o.name, 200, 200)"/>

        :param type: Accepted types: 'Codabar', 'Code11', 'Code128', 'EAN13', 'EAN8', 'Extended39',
        'Extended93', 'FIM', 'I2of5', 'MSI', 'POSTNET', 'QR', 'Standard39', 'Standard93',
        'UPCA', 'USPS_4State'
        :param humanreadable: Accepted values: 0 (default) or 1. 1 will insert the readable value
        at the bottom of the output image
        """
        try:
            barcode = request.env['report'].barcode(type, value, width=width, height=height,
                                                    humanreadable=humanreadable)
        except (ValueError, AttributeError):
            raise exceptions.HTTPException(description='Cannot convert into barcode.')

        return request.make_response(barcode, headers=[('Content-Type', 'image/png')])