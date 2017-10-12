from openerp import models, fields, api
from os import getenv
import pymssql
from datetime import datetime
import time
import csv
import sys
import os
import urllib2
import ftplib
import re

reload(sys)

sys.setdefaultencoding('utf8')

# Connection information
server = '81.20.70.188'
username = 'FTPDELTO'
password = 'D3ltAt3aM2'
delim = ";"

stevec1 = 0
stevec2 = 1


def floatToString(inputValue):
    if type(inputValue)==type(""):
        return inputValue
    else:
        return ('%.2f' % inputValue).rstrip('.')


def format_model_12(part_code):
    new_part_code = part_code
    re.sub('\s+', ' ', new_part_code)
    new_part_code = part_code.replace(" ", "")
    new_part_code = part_code.replace("-", "")
    new_part_code = part_code.replace(' ', '')
    new_part_code = part_code.replace('-', '')

    new_part_code.decode("utf-8")
    if new_part_code == '            ':
        new_part_code = ''
        # print "product", new_part_code
    return new_part_code


# FIND FIRST ELEMENT ELEMENT AND APPEND IT
def find_last(new_default_code, all_products, full_products):
    # product_old_cat = self.search(cr, uid, ['|',('active', '=', False),('active', '=', True),("new_default_code", "=",  default_code)],  context=context)
    product_info = False
    if new_default_code:
        for product in full_products:
            if new_default_code == product['default_code']:
                product_info = product
            else:
                continue

                # print "product_info", product_info
        if product_info == False:

            for product in full_products:
                if new_default_code == product['new_default_code']:
                    product_info = product
                if new_default_code == product['default_code']:
                    return
        else:

            # RECURSIVE
            all_products.append(product_info)
            # print "all_products",all_products

            if product_info['default_code'] == product_info['new_default_code']:
                return

            if product_info['new_default_code'] == '':
                return
            else:

                last_element = find_last(product_info['new_default_code'], all_products, full_products)

class klasifikacija(models.Model):
    _name = "klasifikacija"
    name = fields.Char('Skupina')
    skupina_id = fields.Many2one('Course','Povezava na pricelist')


class razni_klasifikatorji(models.Model):
    _name = "razni_klasifikatorji"
    course_id = fields.Many2one('Course','Povezava na pricelist')
    name = fields.Char('Ime')
    klasifikacija_ids = fields.One2many('klasifikacija',inverse_name='skupina_id',string='Klasifikacija',ondelete='cascade')
    faktor = fields.Char('Faktor')

class Course(models.Model):
    _name = 'pricelist_ypec.verzija'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description", required=True)

    razno_ids = fields.One2many('razni_klasifikatorji', inverse_name='course_id', string='Razni klasifikatorji',ondelete='cascade')

    about = fields.Char(string="About",)
    distributor_code = fields.Char(string="Distributor code: ")
    receiver = fields.Char(string="Receiver: ")
    filename_code = fields.Char(string="Filename code: ")
    language_id = fields.Char(string="Language id: ")
    distributor_code_ymc = fields.Char(string="Distributor code ymc: ")
    vat_rate = fields.Char(string="Vat rate: ")
    currency = fields.Char(string="Currency: ")
    price_start = fields.Char(string="Price start date: ")

    border = fields.Char(string="Meja: ")
    factor_low = fields.Char(string="Spodnji faktor: ")
    factor_high = fields.Char(string="Zgornji faktor: ")
    razred1_border = fields.Char(string="Razred 1 meja: ")
    razred1_factor = fields.Char(string="Razred 1 faktor: ")
    razred2_border = fields.Char(string="Razred 2 meja: ")
    razred2_factor = fields.Char(string="Razred 2 faktor: ")
    razred3_border = fields.Char(string="Razred 3 meja: ")
    razred3_factor = fields.Char(string="Razred 3 faktor: ")
    razred4_border = fields.Char(string="Razred 4 meja: ")
    razred4_factor = fields.Char(string="Razred 4 faktor: ")
    tecaj = fields.Char(string="Tecaj")
    accesories_factor = fields.Char(string="Faktor doddatne opreme: ")
    #test123
    posebno_orodje = fields.Char(string="Faktor posebnega orodja: ")
    #chk = fields.Char(string="Faktor Chain: ")
    batarije = fields.Char(string="Faktor Batarije / kufri / chain: ")

    akrapovic = fields.Char(string="Akrapovic: ")
    tekmovalni_deli = fields.Char(string="Tekmovalni deli: ")
    denbol_oprema = fields.Char(string="Denbol oprema: ")
    dodatna_oprema_akcije = fields.Char(string="Dodatna oprema akcije: ")
    oblacila_dealer = fields.Char(string="Delovna oblacila: ")
    vi_pos_oprema = fields.Char(string="VI POS oprema: ")
    marine_olja = fields.Char(string="Marine olja: ")
    moto_olja = fields.Char(string="Moto olja: ")
    smb_olja = fields.Char(string="SMB olja: ")
    sredstva_nego = fields.Char(string="Sredstva za nego: ")
    ploscice = fields.Char(string="Ploscice: ")
    svecke = fields.Char(string="Svecke: ")
    TW_steel = fields.Char(string="TW Steal stari:")
    TW_steel_old = fields.Char(string="TW Steal novi:")
    peta = fields.Char(string="Peta: ")
    celade = fields.Char(string="Celade: ")



    def create_csv(self, cr, uid, full_products, csv_file, context=None):
        start = time.time()
        reload(sys)
        sys.setdefaultencoding('utf8')
        if os.path.exists(csv_file):
            os.unlink(csv_file)
        fieldnames = ['default_code', 'new_default_code', 'last_default_code', 'opis', 'nabavna', 'koncna','dealer_price','skupina','countryorigin','weight','volume','length','width','heigth','minimumquantity','bucketquantity','stockYAMAHA','discountinued','partsstatus']

        writer_row = "{'default_code': str(product['default_code']).decode('windows-1252'),'new_default_code':str(product['new_default_code']).decode('windows-1252'),'last_default_code':str(product['last_default_code']).decode('windows-1252'),'opis':str(product['opis']),'nabavna':str(product['nabavna']),'koncna':str(product['koncna']),'skupina':product['skupina'],'countryorigin':product['countryorigin'],'weight':product['weight'],'volume':product['volume'],'length':product['length'],'width':product['width'],'heigth':product['heigth'],'minimumquantity':product['minimumquantity'],'bucketquantity':product['bucketquantity'],'stockYAMAHA':product['stockYAMAHA'],'discountinued':product['discountinued'],'partsstatus':product['partsstatus'] }"
        delim = ";"
        #print "---------CREATE CSV  ---------------------------"
        with open(csv_file, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=delim, fieldnames=fieldnames)
            writer.writeheader()

        for product in full_products:
            with open(csv_file, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, delimiter=delim, fieldnames=fieldnames)
                writer.writerow(eval(writer_row))
        end = time.time()
        elapsed = end - start
        print "---------CREATE CSV---( Cas:", str(round(float(elapsed) / 60, 2)), "min  ) ------"


    def generate_supersession(self, cr, uid, ids, context=None):

        full_products = []

        with open('/home/staging/ceniki/S005050.prc') as csvfile:
            data = csvfile.readlines()

            for vrstica in data:
                kataloska = vrstica[5:17]
                naslednik = vrstica[47:59]
                zadnja = ''
                opis = vrstica[17:47]
                nabavna = vrstica[59:68]
                #print vrstica,nabavna,type(nabavna)
                nabavna = float(nabavna)
                nabavna = (nabavna / 100)
                skupina = vrstica[126:132]
                #if skupina[:1] == '2':
                product_info = {}

                product_info['opis'] = opis
                product_info['nabavna'] = nabavna
                product_info['koncna'] = ""
                product_info['default_code'] = format_model_12(kataloska)
                product_info['new_default_code'] = format_model_12(naslednik)
                product_info['skupina'] = skupina
                product_info['countryorigin'] = vrstica[115:118]

                product_info['weight'] = vrstica[81:88]
                product_info['volume'] = vrstica[88:95]
                product_info['length'] = vrstica[95:100]
                product_info['width'] = vrstica[100:105]
                product_info['heigth'] = vrstica[105:110]
                product_info['minimumquantity'] = vrstica[68:71]
                product_info['bucketquantity'] = vrstica[110:115]
                product_info['stockYAMAHA'] = vrstica[121:122]
                product_info['discountinued'] = vrstica[125:126]
                product_info['partsstatus'] = vrstica[122:125]
                #test


                full_products.append(product_info)
        # print full_products
        start = time.time()
        num = 1
        # print "len", len(full_products)
        print "LAST RELATED DEFAULT CODE-----------START---------------------------"
        for product in full_products:
            start = time.time()
            print "num ", num, " ", str(round(float(num) / float(len(full_products)) * 100, 2)), "%"
            num += 1
            all_products = []
            # print product
            # if product['new_default_code'] == '            ':
            #	print "product", product['default_code']
            if product['new_default_code'] != '':
                if product['new_default_code'] == '999999999900':
                    product['last_default_code'] = '999999999900'
                    continue
                else:
                    related_default_code_list = find_last(product['new_default_code'], all_products, full_products)
                    # print "catalog_number", product
                    # print "related", all_products[-1]['default_code']
            else:
                product['last_default_code'] = ''
                continue

            if len(all_products) > 0:

                product['last_default_code'] = all_products[-1]['default_code']
            else:
                product['last_default_code'] = ''

        end = time.time()
        elapsed = end - start
        date_created = datetime.now().strftime("%Y%m%d")
        file_pricelist = '/home/staging/ceniki/'+date_created+'_pricelist.csv'
        print "---------END LAST RELATED DEFAULT CODE---( Cas:", str(round(float(elapsed) / 60, 2)), "min  ) ------"
        self.create_csv(cr, uid, full_products, file_pricelist)

    def generate_txt(self,cr, uid, ids, context=None):

        ypec = self.browse(cr, uid, ids, context=context)
        date_created = datetime.now().strftime("%Y%m%d")
        time_created = datetime.now().strftime("%H%M%S")
        print "---------CREATE TXT COUNTRY FILE---------"
        start = time.time()
        reload(sys)
        i = 1
        vat_rate = float(ypec.vat_rate)
        with open('/home/staging/ceniki/general2.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            record0000 = "0000" + ypec.distributor_code + ypec.receiver + "  " + ypec.filename_code + "  " + date_created + time_created + "                                        "
            f = open('/home/staging/ceniki/generated_csv/' + ypec.name + '-' + date_created + '-' + '.txt', 'a')
            f.write(record0000 + os.linesep)  # python will convert \n to os.linesep

            for vrstica in readCSV:
                kataloska = vrstica[0]
                naslednik = vrstica[1]
                zadnja = vrstica[2]
                opis = vrstica[3]
                vpc = vrstica[5]
                mpc = vrstica[6]
                dealer_vpc = vrstica[7]
                #if ypec.name == 'HR' or ypec.name == 'SI':
                dealer_mpc = vrstica[8]
                #else:
                #    dealer_mpc = 0
                #print kataloska, naslednik, zadnja, vpc, mpc, dealer_vpc, dealer_mpc
                kataloska = kataloska + "               "
                naslednik = naslednik + "               "
                zadnja = zadnja + "               "
                if dealer_mpc == "":
                    dealer_mpc = "0000000000000"

                record2000 = "2000" + str(kataloska[0:15]) + str(ypec.language_id) + str(opis) + "             "
                f.write(record2000 + os.linesep)
                record2010 = "2010" + kataloska[0:15] + naslednik[0:15] + zadnja[0:15] + date_created + "0000000000" + ypec.distributor_code_ymc + "         "
                f.write(record2010 + os.linesep)
                #MPC STRANKA
                koncna_mpc = "{0:.2f}".format(float(mpc)).replace('.', '')
                koncna_mpc = "0000000000000" + str(koncna_mpc)
                koncna_mpc = str(koncna_mpc[-13:])
                #VPC STRANKA
                koncna_vpc = "{0:.2f}".format(float(vpc)).replace('.', '')
                koncna_vpc = "0000000000000" + str(koncna_vpc)
                koncna_vpc = str(koncna_vpc[-13:])
                #Dealer MPC
                dealer_price_mpc = "{0:.2f}".format(float(dealer_mpc)).replace('.', '')
                dealer_price_mpc = "0000000000000" + str(dealer_price_mpc)
                dealer_price_mpc = str(dealer_price_mpc[-13:])
                # Dealer VPC
                dealer_price_vpc = "{0:.2f}".format(float(dealer_vpc)).replace('.', '')
                dealer_price_vpc = "0000000000000" + str(dealer_price_vpc)
                dealer_price_vpc = str(dealer_price_vpc[-13:])
                vat_rate = str(ypec.vat_rate)
                record2020 = "2020" + koncna_vpc + koncna_mpc + dealer_price_vpc + dealer_price_mpc + "0" + vat_rate + "00" + ypec.currency + ypec.price_start + "        "
                f.write(record2020 + os.linesep)
                i += 3
            stevec = i
            stevec += 1
            stevec = "          " + str(stevec)
            record9999 = "9999" + str(stevec[-10:]) + "                                                        "
            f.write(record9999 + os.linesep)
            f.close()
            end = time.time()
            elapsed = end - start
            print "---------CREATE TXT COUNTRY FILE---( Cas:", str(round(float(elapsed) / 60, 2)), "min  ) ------"

    def read_klasifikators(self, cr, uid, ids, context=None):
        print "---------CREATE CSV COUNTRY FILE   START----------------------"


        def create_csv1(ypec, vrstica, dealer_final,customer_final):
            #print "dealer final1", dealer_final, "customer final1: ", customer_final
            path='/home/staging/ceniki/generated_csv/'+ypec.name + '-' + date_created + '.csv'

            kataloska = vrstica[0].replace(' ','')
            naslednik = vrstica[1].replace(' ','')
            zadnja = vrstica[2].replace(' ','')
            opis = vrstica[3]
            nabavna = float(vrstica[4])
            davek = float(ypec.vat_rate) / 100 + 1
            tecaj = float(ypec.tecaj)


            if ypec.name == "SI":
                dealer_vpc = float(dealer_final) / davek
                dealer_mpc = float(dealer_final)

            elif ypec.name == "HR":
                dealer_vpc = (float(dealer_final) * tecaj) / davek
                dealer_mpc = float(dealer_final) * tecaj
            else:
                dealer_vpc = float(dealer_final)
                dealer_mpc = ''

            #print "dealer final", dealer_final, "customer final: ", customer_final



            if nabavna > float(ypec.razred4_border):
                customer_final *= 1
                # print nabavna, " vecje od 4 meje: " + str(float(self.razred4_border))
            else:
                # print nabavna, " manjse od 4 meje: " + str(float(self.razred4_border))
                # print nabavna, "----------------1---------------------"
                if nabavna < float(ypec.razred4_border):
                    # print nabavna, " vecje od 3 meje: " + str(float(self.razred3_border))
                    if nabavna < float(ypec.razred3_border):
                        if nabavna < float(ypec.razred2_border):
                            if nabavna < float(ypec.razred1_border):
                                customer_final *= float(ypec.razred1_factor)
                                # print nabavna, "----------------2---------------------"
                            else:
                                customer_final *= float(ypec.razred2_factor)
                                # print nabavna, "----------------3---------------------"
                        else:
                            customer_final *= float(ypec.razred3_factor)
                            # print nabavna, "----------------4---------------------"
                    else:
                        customer_final *= float(ypec.razred4_factor)

            koncna_vpc = (float(customer_final) * tecaj) / davek
            koncna_mpc = float(customer_final) * tecaj

            #print "nabavna: ",nabavna,"DAVEK:", davek,"DEALER VPC:", dealer_vpc, "DEALER MPC:", dealer_mpc, "Koncna VPC:", koncna_vpc, "koncna MPC:", koncna_mpc
            writer_row = "{'default_code':kataloska, 'new_default_code':naslednik ,'last_default_code':zadnja,'nabavna': str(nabavna),'opis':opis,'koncna_vpc': koncna_vpc, 'koncna_mpc':koncna_mpc ,'dealer_price_vpc':dealer_vpc, 'dealer_price_mpc':dealer_mpc}"
            delim = ";"

            with open(path, 'a') as csvfile:
                fieldnames = ['default_code', 'new_default_code', 'last_default_code', 'opis','nabavna','koncna_vpc', 'koncna_mpc', 'dealer_price_vpc', 'dealer_price_mpc']
                writer = csv.DictWriter(csvfile, delimiter=delim, fieldnames=fieldnames)
                writer.writerow(eval(writer_row))

        #vat_rate = float(self.vat_rate)
        ypec = self.browse(cr, uid, ids, context=context)
        list = []
        for x in ypec.razno_ids:

            # print "klasifikacija: ",x.name
            for y in x.klasifikacija_ids:
                # print "Skupine: ", y.name, " faktor: ", x.faktor
                seznam = {}
                seznam['klasifikator'] = y.name
                seznam['faktor'] = x.faktor
                list.append(seznam)

        list_imen = []
        for x in ypec.razno_ids:

            # print "klasifikacija: ",x.name
            for y in x.klasifikacija_ids:
                # print "Skupine: ", y.name, " faktor: ", x.faktor
                seznam = {}
                seznam['ime'] = x.name
                seznam['faktor'] = x.faktor
                list_imen.append(seznam)


        #print list

        with open('/home/staging/ceniki/general.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            next(readCSV, None)

            date_created = datetime.now().strftime("%Y%m%d")
            time_created = datetime.now().strftime("%H%M%S")
            start = time.time()
            nabavna = 0
            for vrstica in readCSV:
                nabavna = float(vrstica[4])

                #print nabavna, type(nabavna)


                kataloska_s = vrstica[0].replace(' ', '')
                #print "-------------------------------------------vrstica--------------------------------------------------"
                #print vrstica
                if vrstica == '':
                    return
                #print "prej nabavna", nabavna
                skupina = vrstica[7]
                y = skupina[0:1]
                #print y


                def in_dictlist((key, value), my_dictlist):
                    for this in my_dictlist:
                        #print "this: ",this," this[key]: ",this[key]," value:",value
                        if this[key] == value:
                            return this
                    return {}

                rezultat = False
                if in_dictlist(('klasifikator',kataloska_s),list):
                    rezultat = in_dictlist(('klasifikator', kataloska_s), list)

                elif in_dictlist(('klasifikator',skupina),list):
                    rezultat = in_dictlist(('klasifikator', skupina), list)

                else:

                    rezultat = in_dictlist(('klasifikator', y), list)

                    #print "rezultat pred: ",rezultat
                    if rezultat['klasifikator'] == '2':
                        #print "rezervni del"
                        if float(nabavna) < float(ypec.border):

                            rezultat = in_dictlist(('ime', 'Rezervni deli pod mejo'), list_imen)

                        else:
                            rezultat = in_dictlist(('ime', 'Rezervni deli nad mejo'), list_imen)

                if rezultat:
                    #print "nabavna: ",nabavna
                    #print "rezultat: ",rezultat

                    nabavna *= float(rezultat['faktor'])

                    dealer_final = nabavna
                    customer_final = nabavna
                    #print "SELF",ypec
                    #print "dealer final",dealer_final,"customer final: ", customer_final
                    create_csv1(ypec,vrstica,dealer_final,customer_final)

                    #print rezultat


                else:
                    #nabavna = 99999
                    print "ni naslo"

            end = time.time()
            elapsed = end - start
            print "---------CREATE CSV---( Cas:", str(round(float(elapsed) / 60, 2)), "min  ) ------"


            #print "po izracunu",nabavna
