# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

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
                    'year': self.year,
                    'template_id': fixed.template_id.id
                }
                fixed_cost.append((0,0,line))

            for variable in variable_cost_ids:
                line = {
                    'cost_id': variable.id,
                    'trimester': self.trimester,
                    'year': self.year,
                    'template_id': variable.template_id.id
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

    start_date = fields.Date(string="Fecha de Inicio",related="aircraft_id.start_date")
    final_date = fields.Date(string="Fecha Final",related="aircraft_id.final_date")
    months_duration = fields.Float(string="Duracion(Meses)",related="aircraft_id.months_duration")

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
    template_id = fields.Many2one(related='cost_id.template_id', string="Plantilla")
    value_ids = fields.One2many(
        'aff.fixed.cost.value', 'fixed_line_id', 
        string="Variables de Costeo", compute="_compute_value_ids", store=True, readonly=False
    )

    @api.depends('cost_id', 'template_id')
    def _compute_value_ids(self):
        for record in self:
            if not record.template_id:
                record.value_ids = [(5, 0, 0)]
                continue
            existing_vars = record.value_ids.mapped('variable_id.id')
            new_lines = []
            for var in record.template_id.variable_ids:
                if var.id not in existing_vars:
                    new_lines.append((0, 0, {
                        'variable_id': var.id,
                        'value_float': 0.0,
                        'value_integer': 0,
                        'field_type': var.field_type,
                    }))
            if new_lines:
                record.value_ids = new_lines

    def action_execute_formula(self):
        """Evalúa la fórmula de la plantilla y asigna el resultado a los meses"""
        for record in self:
            if not record.template_id or not record.template_id.formule:
                continue
            
            # 1. Construimos el diccionario de variables con sus valores reales ingresados
            localdict = {}
            for val in record.value_ids:
                localdict[val.variable_id.code] = val.value_integer if val.field_type == 'integer' else val.value_float
            
            try:
                # 2. Ejecutamos la fórmula matemáticamente de forma segura
                result = float(safe_eval(record.template_id.formule, localdict))
                
                # 3. Asignamos el resultado a los meses correspondientes de este registro
                # Puedes decidir si la fórmula aplica a todos los meses o si creas variables por mes.
                # En este ejemplo, el cálculo se mapea directo a los campos mensuales:
                record.update({
                    'january': result, 'february': result, 'march': result,
                    'april': result, 'may': result, 'june': result,
                    'july': result, 'august': result, 'september': result,
                    'october': result, 'november': result, 'december': result,
                })
            except Exception as e:
                raise ValidationError(_("Error al evaluar la fórmula en el rubro %s: %s") % (record.cost_id.name, str(e)))

    @api.onchange('value_ids')
    def _onchange_calculate_values_from_formula(self):
        """
        Detecta cambios en caliente dentro de la tabla de variables,
        ejecuta la fórmula y actualiza los meses en tiempo real en la pantalla.
        """
        for record in self:
            if not record.template_id or not record.template_id.formule:
                continue
            
            # 1. Armamos el diccionario clave-valor con los códigos de las variables
            localdict = {}
            for val in record.value_ids:
                localdict[val.variable_id.code] = val.value_integer if val.field_type == 'integer' else val.value_float
            try:
                # 2. Evaluamos la fórmula de manera segura
                result = float(safe_eval(record.template_id.formule, localdict))
                
                # 3. Inyectamos el resultado en los meses de la pantalla
                record.update({
                    'january': result, 'february': result, 'march': result,
                    'april': result, 'may': result, 'june': result,
                    'july': result, 'august': result, 'september': result,
                    'october': result, 'november': result, 'december': result,
                })
            except Exception as e:
                # Evitamos levantar un error intrusivo mientras el usuario digita a medias
                pass

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
    template_id = fields.Many2one(related='cost_id.template_id', string="Plantilla")
    value_ids = fields.One2many(
        'aff.variable.cost.value', 'variable_line_id', 
        string="Variables de Costeo", compute="_compute_value_ids", store=True, readonly=False
    )

    @api.depends('cost_id', 'template_id')
    def _compute_value_ids(self):
        for record in self:
            if not record.template_id:
                record.value_ids = [(5, 0, 0)]
                continue
            existing_vars = record.value_ids.mapped('variable_id.id')
            new_lines = []
            for var in record.template_id.variable_ids:
                if var.id not in existing_vars:
                    new_lines.append((0, 0, {
                        'variable_id': var.id,
                        'value_float': 0.0,
                        'value_integer': 0,
                        'field_type': var.field_type,
                    }))
            if new_lines:
                record.value_ids = new_lines

    def action_execute_formula(self):
        """Evalúa la fórmula de la plantilla y asigna el resultado a los meses"""
        for record in self:
            if not record.template_id or not record.template_id.formule:
                continue
            
            localdict = {}
            for val in record.value_ids:
                localdict[val.variable_id.code] = val.value_integer if val.field_type == 'integer' else val.value_float
            
            try:
                result = float(safe_eval(record.template_id.formule, localdict))
                record.update({
                    'january': result, 'february': result, 'march': result,
                    'april': result, 'may': result, 'june': result,
                    'july': result, 'august': result, 'september': result,
                    'october': result, 'november': result, 'december': result,
                })
            except Exception as e:
                raise ValidationError(_("Error al evaluar la fórmula en el rubro %s: %s") % (record.cost_id.name, str(e)))

    @api.onchange('value_ids')
    def _onchange_calculate_values_from_formula(self):
        """
        Detecta cambios en caliente dentro de la tabla de variables,
        ejecuta la fórmula y actualiza los meses en tiempo real en la pantalla.
        """
        for record in self:
            if not record.template_id or not record.template_id.formule:
                continue
            
            # 1. Armamos el diccionario clave-valor con los códigos de las variables
            localdict = {}
            for val in record.value_ids:
                localdict[val.variable_id.code] = val.value_integer if val.field_type == 'integer' else val.value_float
            try:
                # 2. Evaluamos la fórmula de manera segura
                result = float(safe_eval(record.template_id.formule, localdict))
                
                # 3. Inyectamos el resultado en los meses de la pantalla
                record.update({
                    'january': result, 'february': result, 'march': result,
                    'april': result, 'may': result, 'june': result,
                    'july': result, 'august': result, 'september': result,
                    'october': result, 'november': result, 'december': result,
                })
            except Exception as e:
                # Evitamos levantar un error intrusivo mientras el usuario digita a medias
                pass