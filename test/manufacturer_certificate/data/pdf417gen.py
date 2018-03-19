# -*- coding: utf-8 -*-
import treepoem


text = """HRVHUB30\n
HRK\n
000000000012355\n
ZELJKO SENEKOVIC\n
IVANECKA ULICA 125\n
42000 VARAZDIN\n
2DBK d.d.\n
ALKARSKI PROLAZ 13B\n
21230 SINJ\n
HR1210010051863000160\n
HR01\n
7269-68949637676-00019\n
COST\n
Troskovi za 1. mjesec\n"""





image = treepoem.generate_barcode(
	barcode_type='pdf417',  # One of the BWIPP supported codes.
	data=text,
	options={},
	)
image.save('barcode.png')

