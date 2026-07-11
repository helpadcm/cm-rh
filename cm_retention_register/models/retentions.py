# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class retentions(models.Model):
    _name = 'retentions'
    _order = 'name desc'
    _description = "Detalle de retenciones"
	
    name = fields.Char(string='Numero Retencion')
    partner_name = fields.Char(string='Nombre')
    partner_rtn = fields.Char(string='RTN')
    doc_issue_date = fields.Date(string='Fecha del Asunto')
    active = fields.Boolean(string='Activo',default=True)
    cai_range = fields.Char(string='Rango CAI',)
    date = fields.Date(string='Fecha de retencion')
    pay_number = fields.Many2one('account.payment', 'Ref. de Pago')
    pay_number_check = fields.Many2one('mcheck.mcheck', 'Ref. Numero de pago')
    total_lines = fields.Char(string='Total en lineas')#,compute=_get_total)
    description = fields.Char(string='Descripcion',copy=False,)
    retention_lines = fields.One2many('account.payment.retention.line','retention_id',required=True)
    cai = fields.Many2one('management.cai',string='Cai ')
    cai_ret = fields.Char(string='Numero Ret')
    cai_ret_id = fields.Many2one('management.cai',string='Cai Retencion')
    min_number_shot = fields.Char(string='Rango Minimo')
    max_number_shot = fields.Char(string='Rango Maximo')
    cai_expires_shot = fields.Date(string="Fecha expiracion Ret")
    cai_shot = fields.Char(string='Numero Cai')

    company_id = fields.Many2one('res.company',string='Company',)
    user_id = fields.Many2one('res.users',string='User',)

    sequence_id = fields.Many2one('ir.sequence',string='Secuencia')
    amounttext = fields.Char(string='Total Letras')#,compute=_get_totalt)
    invoice_id = fields.Many2one('account.move', string='Factura')
    ref_doc_type = fields.Selection([
            ('invoice','Factura'),
            ('receipt','Recibo'),
            ('ticket','Ticket'),
            ('sales_ticket','Sales Ticket'),
            ('rent_receipt','Rent Receipt'),
            ('fees_receipt','Fees Receipt'),
            ('account_state','Estado de Cuenta'),],string='Document')
    state = fields.Selection([
            ('draft','Borrador'),
            ('close','Cerrado'),
            ('cancel','Cancelado'),],string='Estado',default="draft")

    doc_type = fields.Selection([
        ('check','Check'),
        ('voucher','Voucher'),
        ],default='Tipo por defecto')

class AccountPaymentRetentionLine(models.Model):
    _name = 'account.payment.retention.line'
    _description = 'Lineas de retencion en pagos'

    payment_id = fields.Many2one('account.payment', required=True, ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Cuenta de Retencion', required=True)
    name = fields.Char(string="Descripcion")
    percentage = fields.Float(string='Percentaje', required=True)
    amount = fields.Monetary(string='Monto')
    currency_id = fields.Many2one(related='payment_id.currency_id', string="Moneda", store=True, readonly=True)
    amount_currency = fields.Float(string='Importe en Divisa')
    company_currency_id = fields.Many2one('res.currency', string="Moneda de la empresa")
    retention_id =  fields.Many2one('retentions', string="Retencion")
    base_amount = fields.Float(string='Monto Base')
    invoice_id = fields.Many2one('account.move', string='Factura')