# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime

class costSheets(models.Model):
    _name = 'aff.cost.sheets'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Hoja de costos"

    name = fields.Char(string="Nombre")
    initial_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha Final")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    year = fields.Char(string="Año")
    line_ids = fields.One2many('aff.cost.sheets.lines','sheet_id',string="Lineas")

    @api.onchange('initial_date', 'final_date')
    def get_trimester(self):
        if self.initial_date and self.final_date:
            if self.initial_date.month == 1 and self.final_date.month == 3:
                self.trimester = '1'
                self.name = f"""1er trimestre {self.initial_date.year}"""
                self.year = self.initial_date.year
            elif self.initial_date.month == 4 and self.final_date.month == 6:
                self.trimester = '2'
                self.name = f"""2do trimestre {self.initial_date.year}"""
                self.year = self.initial_date.year
            elif self.initial_date.month == 7 and self.final_date.month == 9:
                self.trimester = '3'
                self.name = f"""3er trimestre {self.initial_date.year}"""
                self.year = self.initial_date.year
            elif self.initial_date.month == 10 and self.final_date.month == 12:
                self.trimester = '4'
                self.name = f"""4to trimestre {self.initial_date.year}"""
                self.year = self.initial_date.year
            else:
                raise ValidationError("La fecha inicial o final no estan dentro de los valores esperados")

    def create_lines(self):
        print ("////////////////////////////////////////")
        aircraft_ids = self.env['aff.aircraf'].search([])
        fixed_cost_ids = self.env['aff.costs'].search([('cost_type','=','fixed')])
        variable_cost_ids = self.env['aff.costs'].search([('cost_type','=','variable')])
        for aircraf in aircraft_ids:
            fixed_cost = []
            variable_cost = []
            values = {
                'sheet_id': self.id,
                'aircraft_id': aircraf.id,
                'trimester': self.trimester,
                'year': self.year
            }
            for fixed in fixed_cost_ids:
                line = {
                    'cost_id': fixed.id,
                    'trimester': self.trimester,
                    'year': self.year
                }
                fixed_cost.append((0,0,line))

            for variable in variable_cost_ids:
                line = {
                    'cost_id': variable.id,
                    'trimester': self.trimester,
                    'year': self.year
                }
                variable_cost.append((0,0,line))

            if fixed_cost:
                values.update({'fixed_cost_ids': fixed_cost})

            if variable_cost:
                values.update({'variable_cost_ids': variable_cost})

            self.env['aff.cost.sheets.lines'].create(values)


class costSheetsLines(models.Model):
    _name = 'aff.cost.sheets.lines'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Lineas hoja de costos"

    sheet_id = fields.Many2one('aff.cost.sheets',string="Hoja de costo")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    aircraft_id = fields.Many2one('aff.aircraf',string="Aeronave")
    year = fields.Char(string="Año")
    fixed_cost_ids = fields.One2many('fixed.cost.lines','line_id',string="Costos Fijos")
    variable_cost_ids = fields.One2many('variable.cost.lines','line_id',string="Costos Variables")

class fixedCostLines(models.Model):
    _name = 'fixed.cost.lines'
    _description = "Lineas de costo fijo"

    line_id = fields.Many2one('aff.cost.sheets.lines',string="Linea de costo")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    year = fields.Char(string="Año")
    cost_id = fields.Many2one('aff.costs',string="Costo fijo")
    description = fields.Char(string="Descripcion", related='cost_id.description')
    january = fields.Float(string="Enero")
    february = fields.Float(string="Febrero")
    march = fields.Float(string="Marzo")
    april = fields.Float(string="Abril")
    may = fields.Float(string="Mayo")
    june = fields.Float(string="Junio")
    july = fields.Float(string="Julio")
    august = fields.Float(string="Agosto")
    september = fields.Float(string="Septiembre")
    october = fields.Float(string="Octubre")
    november = fields.Float(string="Noviembre")
    december = fields.Float(string="Diciembre")

class variableCostLines(models.Model):
    _name = 'variable.cost.lines'
    _description = "Lineas de costo variable"

    line_id = fields.Many2one('aff.cost.sheets.lines',string="Linea de costo")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    year = fields.Char(string="Año")
    cost_id = fields.Many2one('aff.costs',string="Costo variable")
    description = fields.Char(string="Descripcion", related='cost_id.description')
    january = fields.Float(string="Enero")
    february = fields.Float(string="Febrero")
    march = fields.Float(string="Marzo")
    april = fields.Float(string="Abril")
    may = fields.Float(string="Mayo")
    june = fields.Float(string="Junio")
    july = fields.Float(string="Julio")
    august = fields.Float(string="Agosto")
    september = fields.Float(string="Septiembre")
    october = fields.Float(string="Octubre")
    november = fields.Float(string="Noviembre")
    december = fields.Float(string="Diciembre")