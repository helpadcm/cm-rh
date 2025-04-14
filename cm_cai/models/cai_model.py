# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class managementCai(models.Model):
    _name = "management.cai"
    _description = "Modulo para gestion de cai"

    name = fields.Char(string="CAI")
    expiration_date = fields.Date(string="Fecha de Expiración")
    is_active =  fields.Boolean(string="Activo")
    company_id = fields.Many2one('res.company', string="Compañia",default=lambda self: self.env.user.company_id)
    supplier_id = fields.Many2one('res.partner',string="Proveedor")
    line_ids = fields.One2many('cai.lines.sequence','cai_id',string="Lineas")
    document_type = fields.Selection([('invoice','Factura'),('purchase','Compra'),('retentions','Retenciones'),('credit_note','Nota de Credito'),('debit_note','Nota de Debito')],string="Tipo de Documento")

class caiLines(models.Model):
    _name = "cai.lines.sequence"
    _description = "Modelo para agregar el cai a las secuencias seleccionadas"
	
    cai_id = fields.Many2one('management.cai')
    sequence_id = fields.Many2one("ir.sequence", "Secuencia")
    selected = fields.Boolean("Seleccionado")
    number_from = fields.Integer("Desde")
    number_to = fields.Integer("Hasta")

    @api.onchange('selected')
    def disable_other_regimes(self):
        if self.selected:
            line_ids = self.search([('sequence_id.name','=',self.sequence_id.name)])
            for regime in line_ids:
                regime.write({'selected':0})
            self.write({'selected':1})
            self.sequence_id.number_next_actual = self.number_from




