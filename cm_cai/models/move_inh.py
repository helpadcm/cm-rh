# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.misc import format_date
import math
import requests

class moveInh(models.Model):
    _inherit = "account.move"

    purchase_order_exempt = fields.Char(string="N° Orden de compra exenta")
    record_exonerated = fields.Char(string="N° Constancia de registro exonerado")
    sag_record = fields.Char(string="N° Registro de la SAG")
    currency_rate = fields.Float(string="Tasa de Cambio",digits=(12, 4),compute="get_currency_rate")
    same_currency = fields.Boolean(string="Misma moneda",compute="get_currency_rate")
    amount_in_words = fields.Char(string="Monto en Letras:",compute="_get_amount_in_words")
    cai_number = fields.Char(string="Cai",copy=False)
    expiration_cai_date = fields.Date(string="Fecha de expiración CAI",copy=False)
    min_number_cai = fields.Char(string="Número máximo",copy=False)
    max_number_cai = fields.Char(string="Número Minímo",copy=False)
    internal_number = fields.Char(string="Numero interno",copy=False,default='Borrador')
    modality = fields.Selection([('upon_delivery','Por Cobrar'),('credit','Credito'),('counted','Contado')], string="Modalidad")

    cai_id = fields.Many2one('management.cai', string='Numero de Cai')

    @api.constrains(lambda self: (self._sequence_field, self._sequence_date_field))
    def _constrains_date_sequence(self):
        # Make it possible to bypass the constraint to allow edition of already messed up documents.
        # /!\ Do not use this to completely disable the constraint as it will make this mixin unreliable.
        constraint_date = fields.Date.to_date(self.env['ir.config_parameter'].sudo().get_param(
            'sequence.mixin.constraint_start_date',
            '1970-01-01'
        ))
        for record in self:
            if not record._must_check_constrains_date_sequence():
                continue
            date = fields.Date.to_date(record[record._sequence_date_field])
            sequence = record[record._sequence_field]
            if record.move_type != 'out_invoice':
                if (sequence and date and date > constraint_date and not record._sequence_matches_date()):
                    raise ValidationError(_(
                        "The %(date_field)s (%(date)s) doesn't match the sequence number of the related %(model)s (%(sequence)s)\n"
                        "You will need to clear the %(model)s's %(sequence_field)s to proceed.\n"
                        "In doing so, you might want to resequence your entries in order to maintain a continuous date-based sequence.",
                        date=format_date(self.env, date),
                        sequence=sequence,
                        date_field=record._fields[record._sequence_date_field]._description_string(self.env),
                        sequence_field=record._fields[record._sequence_field]._description_string(self.env),
                        model=self.env['ir.model']._get(record._name).display_name,
                    ))

    def button_draft(self):
        self.write({'internal_number': self.name})
        res = super(moveInh, self).button_draft()
        self.write({'name': 'Borrador'})
        return res

    @api.depends('posted_before', 'state', 'journal_id', 'date', 'move_type', 'payment_id')
    def _compute_name(self):
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund']:
                if rec.state == 'draft':
                    rec.name = _('/')
            else:
                res = super(moveInh, self)._compute_name()
                return res


    def _post(self, soft=True):
        res = super(moveInh, self)._post(soft=False)
        for inv in self:
            if inv.move_type in ['out_invoice']:
                if inv.journal_id.sequence_id:
                    if inv.journal_id.sequence_id.is_fiscal_sequence:
                        if inv.invoice_date > inv.journal_id.sequence_id.expiration_date:
                            raise ValidationError(_('Fecha de Factura mayor que fecha de expiracion CAI'))

                        cai_id = inv.journal_id.sequence_id.cai_ids.filtered(lambda cai: cai.selected == True)
                        if cai_id:
                            if inv.journal_id.sequence_id.number_next_actual > cai_id.number_to:
                                raise ValidationError('Ha llegado al numero maximo permitido, por favor configurar un nuevo CAI')
                        
                        if inv.internal_number == 'Borrador' or not inv.internal_number:
                            new_name = inv.journal_id.sequence_id.with_context(ir_sequence_date=inv.invoice_date).next_by_id()
                            inv.with_context({'cai': True}).write({'name': new_name})
                            inv.write({'payment_reference': new_name})
                            inv.write({'internal_number': new_name})
                            inv.expiration_cai_date = inv.journal_id.sequence_id.expiration_date
                            inv.min_number_cai = inv.journal_id.sequence_id.dis_min_value
                            inv.max_number_cai = inv.journal_id.sequence_id.dis_max_value
                        
                            for seq in inv.journal_id.sequence_id.cai_ids:
                                if seq.selected:
                                    inv.cai_number = seq.cai_id.name
                        else:
                            inv.write({'name': inv.internal_number})
                    else:
                        if inv.internal_number in ['/', 'Borrador']:
                            new_name = inv.journal_id.sequence_id.with_context(ir_sequence_date=inv.invoice_date).next_by_id()
                            inv.write({'name': new_name})
                            inv.write({'internal_number': new_name})
                        else:
                            inv.write({'name': inv.internal_number})
            if inv.move_type in ['entry']:
                if inv.internal_number != 'Borrador':
                    inv.write({'name': inv.internal_number})
            if inv.move_type in ['in_invoice']:
                if inv.internal_number == 'Borrador' or not inv.internal_number:
                    if inv.journal_id.sequence_id:
                        new_name = inv.journal_id.sequence_id.with_context(ir_sequence_date=inv.invoice_date).next_by_id()
                        inv.write({'payment_reference': new_name})
                        inv.write({'internal_number': new_name})
                else:
                    inv.write({'name': inv.internal_number})
        return res

    @api.depends("currency_id",'invoice_date')
    def get_currency_rate(self):
        for rec in self:
            if rec.currency_id:
                if rec.currency_id != rec.company_id.currency_id:
                    rec.same_currency = False
                    if rec.invoice_date:
                        rate = rec.currency_id.with_context(date=rec.invoice_date)
                        rec.currency_rate = 1 / rate.rate
                    else:
                        rate = rec.currency_id.with_context(date=datetime.now().date())
                        rec.currency_rate = 1 / rate.rate
                else:
                    rec.currency_rate = 1
                    rec.same_currency = True

    @api.depends('amount_total','currency_id')
    def _get_amount_in_words(self):
        for rec in self:
            rec.amount_in_words = ''
            if rec.currency_id:
                if rec.currency_id != rec.company_id.currency_id:
                    amount_signed = rec.amount_total_signed
                    if rec.amount_total_signed < 0:
                        amount_signed = amount_signed * -1
                        
                    if rec.user_id:
                        currency_name = rec.user_id.company_id.currency_id.name
                    else:
                        currency_name = rec.company_id.currency_id.name

                    rec.amount_in_words = rec.to_word(round(amount_signed, 2),currency_name)

                else:
                    rec.amount_in_words = rec.to_word(round(rec.amount_total, 2),rec.currency_id.name)
            else:
                rec.amount_in_words = rec.to_word(round(rec.amount_total, 2),rec.user_id.company_id.currency_id.name)

    def to_word(self,number, mi_moneda):
        valor = number
        number = int(number)
        decimal_value = valor - number

        if decimal_value >= 0.5:
            centavos = math.ceil(round(decimal_value, 2) * 100)
        else:
            if (round(decimal_value,2)) == 0.29:
               centavos = 29
            else:
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

class journalInh(models.Model):
    _inherit = "account.journal"

    sequence_id = fields.Many2one("ir.sequence", string="Secuencia")
    type_document = fields.Selection([('cn','Nota de Credito'),('dn','Nota de Debito'),('inv','Factura'),('ret','Retenciones'),('financing','Financiero')], string="Para Documento")