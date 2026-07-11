# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import math

class saleOrderInherit(models.Model):
    _inherit = 'sale.order'

    purchase_order_exempt = fields.Char(string="N° Orden de compra exenta")
    record_exonerated = fields.Char(string="N° Constancia de registro exonerado")
    sag_record = fields.Char(string="N° Registro de la SAG")

    # def _prepare_invoice(self):
    #     res = super(saleOrderInherit,self)._prepare_invoice()
    #     res.update({
    #         'purchase_order_exempt':self.purchase_order_exempt,
    #         'record_exonerated':self.record_exonerated,
    #         'sag_record':self.sag_record
    #     })
    #     return res

class companyInherit(models.Model):
    _inherit = 'res.company'

    def to_word(self,number, mi_moneda):
        valor = number
        number = int(number)
        decimal_value = round((valor - number), 2)

        # if decimal_value >= 0.5:
        #     centavos = math.ceil(round(decimal_value, 2) * 100)
        # else:
        #     if (round(decimal_value,2)) == 0.29:
        #        centavos = 29
        #     else:
        centavos = int((round(valor-number,2)) * 100)

        #else:
        #    centavos = (round(valor-number,2)) * 100

        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )

        DECENAS = (
            'VENTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN ')

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Costa Rica', 'currency': 'CRC', 'singular': u'Colon', 'plural': u'Colones', 'symbol': u'₡'},
            {'country': u'Guatemala Quetzal', 'currency': 'GTQ', 'singular': u'Quetzal', 'plural': u'Quetzales', 'symbol': u'Q'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
            )
        if mi_moneda != None:
          
            for r in MONEDAS:
               if r['currency'] == mi_moneda:
                   moneda = r
            
            
            #moneda = filter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
            if number < 2:
                moneda = moneda['singular']
            else:
                moneda = moneda['plural']
            
        else:
            moneda = ""
        converted = ''
        if not (0 < number < 999999999):
            return 'No es posible convertir el numero a letras'

        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]

        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % self.convert_group(millones)

        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % self.convert_group(miles)

        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % self.convert_group(cientos)
        converted += moneda
        if(centavos)>0:
            cents = centavos
            if centavos < 10:
                cents = "0%s"%centavos
            converted+= " con %s/100 Centavos"%cents
        elif(centavos) == 0:
            converted+= " con 00/100 Centavos"

            
        #converted += moneda
        return converted.title()

    def convert_group(self,n):
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )
        DECENAS = (
            'VEINTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN '
        )

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Costa Rica', 'currency': 'CRC', 'singular': u'Colon', 'plural': u'Colones', 'symbol': u'₡'},
            {'country': u'Guatemala Quetzal', 'currency': 'GTQ', 'singular': u'Quetzal', 'plural': u'Quetzales', 'symbol': u'Q'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        output = ''

        if(n == '100'):
            output = "CIEN "
        elif(n[0] != '0'):
            output = CENTENAS[int(n[0]) - 1]

        k = int(n[1:])
        if(k <= 20):
            output += UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

        return output