# -*- coding: utf-8 -*-
from odoo import models, fields, api

class sequenceInh(models.Model):
    _inherit = "ir.sequence"
    
    cai_ids   = fields.One2many("cai.lines.sequence", 'sequence_id', "CAI'S")
    start_date		= fields.Date('Fecha de Inicio')
    expiration_date = fields.Date('Fecha de Expiración', compute="get_expiration_date")
    min_value		= fields.Integer('Rango Menor', compute="_get_min_value")
    max_value		= fields.Integer('Rango Mayor', compute="_get_max_value")
    dis_min_value	= fields.Char('Número Minimo',readonly=True, compute='display_min_value')
    dis_max_value	= fields.Char('Número Maximo',readonly=True, compute='display_max_value')
    percentage_alert = fields.Float('Porcentaje de Alerta', default=80)
    percentage = fields.Float('Percentaje', compute='compute_percentage')

    l_prefix = fields.Char('Préfijo', related='prefix')
    vitt_padding = fields.Integer('Relleno Númerico', related='padding')
    vitt_number_next_actual = fields.Integer('Siguiente Número', related='number_next_actual')
    is_fiscal_sequence = fields.Boolean("Secuencia Fiscal")
    
    @api.depends('cai_ids.number_from')
    def _get_min_value(self):
        self.min_value = 0
        for rec in self:
            if rec.cai_ids:
                for regime in rec.cai_ids:
                    if regime.selected:
                        rec.min_value = regime.number_from
            else:
                rec.min_value = 0

    @api.depends('cai_ids.number_to')
    def _get_max_value(self):
        self.max_value = 0
        for rec in self:
            if rec.cai_ids:
                for regime in rec.cai_ids:
                    if regime.selected:
                        rec.max_value = regime.number_to
            else:
                rec.max_value = 0

    
    @api.depends('cai_ids')
    def get_expiration_date(self):
        self.expiration_date = False
        for rec in self:
            if rec.cai_ids:
                for regime in rec.cai_ids:
                    if regime.selected:
                        rec.expiration_date = regime.cai_id.expiration_date


    @api.depends('min_value')
    def display_min_value(self):
        self.dis_min_value = False
        for rec in self:
            if rec.l_prefix:
                start_number_filled = str(rec.min_value)
                for filled in range(len(str(rec.min_value)), rec.vitt_padding):
                    start_number_filled = '0' + start_number_filled
                rec.dis_min_value = rec.l_prefix + str(start_number_filled)


    @api.depends('max_value')
    def display_max_value(self):
        self.dis_max_value = False
        for rec in self:
            if rec.l_prefix:
                final_number = rec.max_value
                final_number_filled = str(rec.max_value)
                for filled in range(len(str(final_number)), rec.vitt_padding):
                    final_number_filled = '0' + final_number_filled
                rec.dis_max_value = rec.l_prefix + str(final_number_filled)

    @api.depends('number_next_actual')
    def compute_percentage(self):
        for rec in self:
            numerator = rec.number_next_actual - rec.min_value
            denominator = rec.max_value - rec.min_value
            if denominator > 0:
                difference = (rec.number_next_actual - rec.min_value) / (rec.max_value - rec.min_value)
                rec.percentage = (difference * 100) - 1
            else:
                rec.percentage = 0
