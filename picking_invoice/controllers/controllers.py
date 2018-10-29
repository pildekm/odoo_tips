# -*- coding: utf-8 -*-
from odoo import http

# class PickingInvoice(http.Controller):
#     @http.route('/picking_invoice/picking_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/picking_invoice/picking_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('picking_invoice.listing', {
#             'root': '/picking_invoice/picking_invoice',
#             'objects': http.request.env['picking_invoice.picking_invoice'].search([]),
#         })

#     @http.route('/picking_invoice/picking_invoice/objects/<model("picking_invoice.picking_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('picking_invoice.object', {
#             'object': obj
#         })