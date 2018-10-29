## Imports
# from StringIO import StringIO
from odoo import api, fields, models, tools, _, exceptions
import struct, datetime, cStringIO, pprint
import base64
import csv
import time
from odoo.addons.sale.models.sale import SaleOrderLine
import pdfminer.layout
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTTextLineHorizontal, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from cStringIO import StringIO
from pdfminer.converter import LTChar, TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

import io


# import logging
# import re
# from odoo.exceptions import ValidationError
# from odoo.osv import expression
# import odoo.addons.decimal_precision as dp

## Get the logger:
## Declare a temporary container:


def prRed(prt): print("\033[91m {}\033[00m".format(prt))


def prGreen(prt): print("\033[92m {}\033[00m".format(prt))


def prYellow(prt): print("\033[93m {}\033[00m".format(prt))


def prLightPurple(prt): print("\033[94m {}\033[00m".format(prt))


def prPurple(prt): print("\033[95m {}\033[00m".format(prt))


def prCyan(prt): print("\033[96m {}\033[00m".format(prt))


def prLightGray(prt): print("\033[97m {}\033[00m".format(prt))


def prBlack(prt): print("\033[98m {}\033[00m".format(prt))


def printDescription(prt): print ("\033[43m {} \033[m".format(prt))


def printBlue(prt): print ("\033[44m {} \033[m".format(prt))


def printGreen(prt): print ("\033[42m {} \033[m".format(prt))


def printRed(prt): print ("\033[41m {} \033[m".format(prt))


# print "42\t\033[42m coloured! \033[m\n"


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        # print "false",s
        return False


def RepresentsFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class Record(object):
    pass


# FUNCTIONS
def str_to_datetime(strdate):
    return datetime.strptime(strdate, tools.DEFAULT_SERVER_DATE_FORMAT)


def fixed_to_data(raw_data, fieldspecs):
    # build the format for struct.unpack
    # fieldspecs.sort(key=lambda x: x[1]) # just in case
    raw_data = raw_data[0]
    unpack_len = 0
    unpack_fmt = ""
    for fieldspec in fieldspecs:
        start = fieldspec[1] - 1
        end = start + fieldspec[2]
        if start > unpack_len:
            unpack_fmt += str(start - unpack_len) + "x"
        unpack_fmt += str(end - start) + "s"
        unpack_len = end
    field_indices = range(len(fieldspecs))
    # print "len ",unpack_len, unpack_fmt
    unpacker = struct.Struct(unpack_fmt).unpack_from
    print "raw_data ", raw_data
    print "unpacker", unpacker
    print "unpack_len", unpack_len
    print "len2", len(raw_data)
    print "if", (len(raw_data) >= unpack_len)
    if ('Order' in raw_data) and ('Invoice' in raw_data) and ('Item' in raw_data) or ('Number' in raw_data) and (
            'Date' in raw_data) and ('Ordered' in raw_data):
        return {}
    if len(raw_data) >= unpack_len:
        f = cStringIO.StringIO(raw_data)
        # headings = f.next()
        # print "headings" ,headings
        for line in f:
            # The guts of this loop would of course be hidden away in a function/method
            # and could be made less ugly

            raw_fields = unpacker(line)
            r = Record()
            for x in field_indices:
                setattr(r, fieldspecs[x][0], fieldspecs[x][3](raw_fields[x]))
            # pprint.pprint(r.__dict__)
            return r.__dict__
    else:

        return {}
    # return False


# functions for converting input fields to usable data
cnv_text = lambda s: s.rstrip()
cnv_int = lambda s: int(s)
cnv_date_dmy = lambda s: datetime.datetime.strptime(s, "%d%m%Y")  # ddmmyyyy
# etc

# field specs (field name, start pos (1-relative), len, converter func)
# TODO: Doloci fielde glede na width
fieldspecs = [
    ('order_number', 0, 5, cnv_text),
    ('invoice_number', 10, 8, cnv_text),
    ('invoice_date', 22, 10, cnv_text),
    ('item_ordered', 36, 12, cnv_text),
    ('item_shipped', 52, 12, cnv_text),
    ('quantity', 68, 4, cnv_text),
    ('unit_price', 80, 8, cnv_text),
    ('case', 92, 4, cnv_text),
]


class Record(object):
    pass


class PickingInvoiceImport(models.TransientModel):
    _name = 'picking.invoice.import'
    _description = 'Picking Invoice Import'

    data = fields.Binary('File')
    name = fields.Char(string='Filename Name')
    delimeter = fields.Char('Delimeter', default='\t', help='Default delimeter is ","')
    invoice_type = fields.Selection([('yamaha', 'Yamaha'), ('ixs', 'IXS'), ('tm', 'TM')], 'Invoice type',
                                    default='yamaha', required=True)

    @api.multi
    def _get_display_price(self, product, product_product, sale_order, quote_data):
        # TO DO: move me in master/saas-16 on sale.order
        if sale_order.pricelist_id.discount_policy == 'with_discount':
            return product_product.with_context(pricelist=sale_order.pricelist_id.id).price
        price, rule_id = sale_order.pricelist_id.get_product_price_rule(product_product,
                                                                        float(quote_data['product_uom_qty']) or 1.0,
                                                                        sale_order.partner_id)
        pricelist_item = self.env['product.pricelist.item'].browse(rule_id)
        if (pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id.discount_policy == 'with_discount'):
            price, rule_id = pricelist_item.base_pricelist_id.get_product_price_rule(product_product,
                                                                                     float(quote_data[
                                                                                               'product_uom_qty']) or 1.0,
                                                                                     sale_order.partner_id)
            return price
        else:
            from_currency = sale_order.company_id.currency_id
            return from_currency.compute(product.lst_price, sale_order.pricelist_id.currency_id)

    @api.one
    def create_yamaha_date(self, date):
        y = date.split('/')
        if len(y) == 3:
            return y[1] + '/' + y[0] + '/' + y[2]
        else:
            return False

    @api.multi
    def create_picking_invoice(self, invoice_data, type):
        picking_invoice = self.env['picking.invoice']
        # TODO USTVARI invoice
        # name,invoice_no,invoice_date,order_line
        invoice_data_values = {
            'name': type + "-" + invoice_data['invoice_number'],
            'invoice_no': invoice_data['invoice_number'],
            'invoice_date': invoice_data['invoice_date'],

        }

        invoice_line_id = picking_invoice.create(invoice_data_values)

        return invoice_line_id

    @api.multi
    def create_picking_invoice_line(self, invoice_data, picking_order_id):
        picking_invoice_line_object = self.env['picking.invoice.line']
        product_product_object = self.env['product.product']
        purchase_order_line_object = self.env['purchase.order.line']
        product_product = product_product_object.search(
            ['|', ('sale_ok', '=', True), ('sale_ok', '=', False), '|', ('active', '=', True), ('active', '=', False),
             ('default_code', '=', invoice_data['item_shipped'])])
        product_id = product_product_object.search(
            ['|', ('sale_ok', '=', True), ('sale_ok', '=', False), '|', ('active', '=', True), ('active', '=', False),
             ('default_code', '=', invoice_data['item_ordered'])], limit=1)
        # if not product_id:
        #	return False
        # TODO: Ustvari invoice line
        # sale_order_line_id sale.order.line
        # qty
        # price_unit
        # item_shipped
        # order_number
        # case_number

        # odstrani state = done iz purchase_order_line_id

        purchase_order_line_id = purchase_order_line_object.search(
            [('product_id', '=', product_id.id), ('ref_number', '=', invoice_data['order_number'])], limit=1)
        invoces_lines = {}
        if len(purchase_order_line_id):
            pack_operation_product = False
            for move_id in purchase_order_line_id.move_ids:
                if move_id.state == 'assigned':
                    for linked_move_operation in move_id.linked_move_operation_ids:
                        pack_operation_product = linked_move_operation.operation_id
                    # order_line.pack_operation_product
            invoice_data_line_values = {
                'qty': invoice_data['quantity'],
                'price_unit': invoice_data['unit_price'],
                'item_shipped': product_product.id or False,
                'order_number': invoice_data['order_number'],
                'case_number': invoice_data['case'],
                'picking_order_id': picking_order_id.id,
                'purchase_order_line_id': purchase_order_line_id.id,
                'pack_operation_product': pack_operation_product.id

            }
            # TODO naredi to kar ni poparckalo -> to pomeni da teh izdelkov ni

            return picking_invoice_line_object.create(invoice_data_line_values)
        else:
            invoice_data_line_values = {
                'qty': invoice_data['quantity'],
                'order_number': invoice_data['order_number'],
                'case_number': invoice_data['case'],
                'price_unit': invoice_data['unit_price'],
                'missing_product_id': product_id.id,
                'picking_order_id': picking_order_id.id,
            }
            return picking_invoice_line_object.create(invoice_data_line_values)

    @api.multi
    def import_picking_invoice(self):
        sale_order_id = self.action_import_picking_invoice()
        return {}

    @api.one
    def import_yamaha_invoice(self):
        start = time.time()
        printDescription("---------NEW START CSV READ")

        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        # invoice_no = self.invoice_no
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = '\t'
        reader = csv.reader(file_input, lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]
        # check if keys exist
        row_count = len(reader_info)
        if not isinstance(keys, list):
            raise exceptions.Warning(
                _("No data"))
        values = {}
        num = 1
        default_code_list = []
        default_code = False
        quote_data = {}

        picking_invoice_id = False
        new_picking_invoice_ids = []
        for i in reader_info:
            #            default_code = i[1]

            num += 1

            # TODO: Pretvori data

            invoice_data_line = fixed_to_data(i, fieldspecs)
            if not invoice_data_line:
                continue
            invoice_data = {}
            if not picking_invoice_id:
                if 'invoice_date' in invoice_data_line:
                    invoice_data_line['invoice_date'] = self.create_yamaha_date(invoice_data_line['invoice_date'])
                picking_invoice_id = self.create_picking_invoice(invoice_data_line, 'Yamaha')
            picking_invoice_line_id = self.create_picking_invoice_line(invoice_data_line, picking_invoice_id)
            if picking_invoice_line_id:
                new_picking_invoice_ids.append(picking_invoice_line_id.id)

        picking_invoice_id.write({'order_line': [(6, 0, new_picking_invoice_ids)]})
        # TODO pelji me v ta view s tem idjem -> picking_invoice_id
        end = time.time()

        elapsed = end - start
        elapsed_min = str(round(float(elapsed) / 60, 2))
        printDescription("END CSV READ--( Cas: " + elapsed_min + " min )--")

    @api.one
    def pdf_to_csv_two(self, filename):

        class CsvConverter(TextConverter):
            def __init__(self, *args, **kwargs):
                TextConverter.__init__(self, *args, **kwargs)

            def end_page(self, i):
                from collections import defaultdict
                lines = defaultdict(lambda: {})
                for child in self.cur_item._objs:
                    if isinstance(child, LTChar):
                        (_, _, x, y) = child.bbox
                        line = lines[int(-y)]
                        line[x] = child._text.encode(self.codec)
                        # the line is now an unsorted dict

                for y in sorted(lines.keys()):
                    line = lines[y]
                    # combine close letters to form columns
                    xpos = tuple(sorted(line.keys()))
                    new_line = []
                    temp_text = ''
                    for i in range(len(xpos) - 1):
                        temp_text += line[xpos[i]]
                        if xpos[i + 1] - xpos[i] > 8:
                            # the 8 is representing font-width
                            # needs adjustment for your specific pdf
                            new_line.append(temp_text)
                            temp_text = ''
                    # adding the last column which also manually needs the last letter
                    new_line.append(temp_text + line[xpos[-1]])

                    self.outfp.write(";".join(nl for nl in new_line))
                    self.outfp.write("\n")

        # ... the following part of the code is a remix of the
        # convert() function in the pdfminer/tools/pdf2text module
        rsrc = PDFResourceManager()
        outfp = StringIO()
        device = CsvConverter(rsrc, outfp, codec="utf-8", laparams=LAParams())

        # fp = open(filename, 'rb')
        fp = filename
        interpreter = PDFPageInterpreter(rsrc, device)
        for i, page in enumerate(PDFPage.get_pages(fp)):
            # outfp.write("START PAGE %d\n" % i)
            if page is not None:
                interpreter.process_page(page)
            # outfp.write("END PAGE %d\n" % i)

        device.close()
        fp.close()

        return outfp.getvalue()

    @api.one
    def pdf_to_csv(self, filename, separator, threshold):

        class CsvConverter(TextConverter):
            def __init__(self, *args, **kwargs):
                TextConverter.__init__(self, *args, **kwargs)
                self.separator = separator
                self.threshold = threshold

            def end_page(self, i):
                from collections import defaultdict
                lines = defaultdict(lambda: {})
                for child in self.cur_item._objs:  # <-- changed
                    if isinstance(child, LTChar):
                        (_, _, x, y) = child.bbox
                        line = lines[int(-y)]
                        line[x] = child._text.encode(self.codec)  # <-- changed
                for y in sorted(lines.keys()):
                    line = lines[y]
                    self.line_creator(line)
                    self.outfp.write(self.line_creator(line))
                    self.outfp.write("\n")

            def line_creator(self, line):
                keys = sorted(line.keys())
                # calculate the average distange between each character on this row
                average_distance = sum([keys[i] - keys[i - 1] for i in range(1, len(keys))]) / len(keys)
                # append the first character to the result
                result = [line[keys[0]]]
                for i in range(1, len(keys)):
                    # if the distance between this character and the last character is greater than the average*threshold
                    if (keys[i] - keys[i - 1]) > average_distance * self.threshold:
                        # append the separator into that position
                        result.append(self.separator)
                    # append the character
                    result.append(line[keys[i]])
                printable_line = ''.join(result)
                return printable_line

        # ... the following part of the code is a remix of the
        # convert() function in the pdfminer/tools/pdf2text module
        rsrc = PDFResourceManager()
        outfp = StringIO()
        device = CsvConverter(rsrc, outfp, codec="utf-8", laparams=LAParams())
        # becuase my test documents are utf-8 (note: utf-8 is the default codec)

        # fp = open(filename, 'rb')
        fp = filename
        interpreter = PDFPageInterpreter(rsrc, device)
        for i, page in enumerate(PDFPage.get_pages(fp)):
            outfp.write("START PAGE %d\n" % i)
            if page is not None:
                interpreter.process_page(page)
            outfp.write("END PAGE %d\n" % i)

        device.close()
        fp.close()

        return outfp.getvalue()

    @api.one
    def create_ixs_date(self, date):
        y = date.split('.')
        if len(y) == 3:
            return y[1] + '/' + y[0] + '/' + y[2]
        else:
            return False

    @api.one
    def import_ixs_invoice(self):
        start = time.time()
        printDescription("---------START IXS Invoice import")
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        separator = ';'

        table_threshold = 0.75

        pdf_data = self.pdf_to_csv_two(file_input)
        # pdf_data = self.pdf_to_csv(file_input, separator, table_threshold)

        rows = (line.split(';') for line in pdf_data)
        d = {row[0]: row[1:] for row in rows}
        # test = [ dict(y.split(':') for y in x.split(',')) for x in 'rows'.split('|')]
        cnv_text = lambda s: s.rstrip()
        cnv_int = lambda s: int(s)
        cnv_float = lambda s: float(s)
        cnv_date_dmy = lambda s: datetime.datetime.strptime(s, "%d%m%Y")  # ddmmyyyy
        fieldspecs_conf = [
            ('No', 3, 4, cnv_text),
            ('ImporterOrderNo', 8, 8, cnv_text),
            ('YMEOrderNo', 19, 8, cnv_text),
            ('PartNo', 28, 16, cnv_text),
            ('PartName', 44, 32, cnv_text),
            ('SupplierCode', 65, 3, cnv_text),
            ('DeliveryQty', 68, 9, cnv_text),
            ('UnitPrice', 79, 11, cnv_text),
            ('AmountinEUR', 92, 11, cnv_text),
            ('TariffCode', 103, 14, cnv_text),
            ('COO', 118, 3, cnv_text),
            ('NettoWeight', 122, 29, cnv_text),
        ]

        # print "pdf_data",pdf_data
        # Poizvedba za st. racuna

        reader = csv.reader(pdf_data[0].split('\n'), delimiter=';')
        all_data = []
        ixs_invoice_all_data = {}
        all_invoice_lines = []
        picking_invoice_id = False
        new_picking_invoice_ids = []
        for row in reader:
            invoice_line = {}
            raw_data = row
            #
            ixs_invoice_data = {}
            picking_invoice_line_id = False
            if len(row) == 2:
                ixs_invoice_all_data[row[0]] = row[1]
                if row[0] == 'Invoice':
                    # TODO - Zakaj zadnje 3
                    ixs_invoice_all_data['invoice_number'] = row[1][-3:]
                if row[0] == 'Date':
                    ixs_invoice_all_data['invoice_date'] = self.create_ixs_date(row[1])

            if len(row) > 7 and 'invoice_number' in ixs_invoice_all_data and 'invoice_date' in ixs_invoice_all_data:
                try:
                    int(row[0])
                    invoice_line['pos'] = row[0]
                    # poberi vse - se
                    invoice_line['item_ordered'] = row[1].replace('-', '')
                    invoice_line['item_shipped'] = row[1].replace('-', '')
                    try:
                        invoice_line['quantity'] = int(row[3])
                    except:
                        try:
                            invoice_line['quantity'] = int(row[4])
                        except:
                            invoice_line['quantity'] = 1
                            pass
                    try:
                        invoice_line['unit_price'] = float(row[5])
                    except:
                        try:
                            invoice_line['unit_price'] = float(row[6])
                        except:
                            pass
                    # invoice_line['unit_price'] = row[5]
                    invoice_line['case'] = 1
                    invoice_line['order_number'] = ixs_invoice_all_data['invoice_number']
                    invoice_line['invoice_number'] = ixs_invoice_all_data['invoice_number']
                    invoice_line['invoice_date'] = ixs_invoice_all_data['invoice_date']
                except:
                    continue

                # invoice_data['item_ordered']
                # invoice_data['order_number']
                # invoice_data['quantity']
                # invoice_data['unit_price']
                # invoice_data['order_number']
                # invoice_data['case']
            if not picking_invoice_id and ixs_invoice_all_data != {} and 'invoice_number' in ixs_invoice_all_data and 'Date' in ixs_invoice_all_data:
                picking_invoice_id = self.create_picking_invoice(ixs_invoice_all_data, 'IXS')
            if invoice_line != {}:
                picking_invoice_line_id = self.create_picking_invoice_line(invoice_line, picking_invoice_id)
            if picking_invoice_line_id:
                new_picking_invoice_ids.append(picking_invoice_line_id.id)

        picking_invoice_id.write({'order_line': [(6, 0, new_picking_invoice_ids)]})
        print ixs_invoice_all_data

    @api.one
    def action_import_picking_invoice(self):
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        if not self.invoice_type:
            raise exceptions.Warning(_("Select invoice type"))
        # TODO naredi za ixs in tm
        if self.invoice_type == 'yamaha':
            self.import_yamaha_invoice()
        elif self.invoice_type == 'ixs':
            self.import_ixs_invoice()
        elif self.invoice_type == 'tm':
            self.import_tm_invoice()
