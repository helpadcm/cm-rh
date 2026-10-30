# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

selection_period = [
    ('annual', 'Anual'),
    ('monthly', 'monthly'),
    ('useful_life', 'Vida Util')
]

selection_forms = [
    ('form01', 'Form 1'),
    ('form02', 'Form 2'),
    ('form03', 'Form 3'),
    ('form04', 'Form 4'),
    ('form05', 'Form 5'),
    ('form06', 'Form 6'),
    ('form08', 'Form 8'),
    ('form10', 'Form 10'),
]

class fixedCostLines(models.Model):
    _name = 'fixed.cost.lines'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Lineas de costo fijo"

    line_id = fields.Many2one('aff.cost.sheets.lines',string="Linea de costo")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    year = fields.Char(string="Año")
    form_type = fields.Selection(selection_forms, string="Forms")
    cost_id = fields.Many2one('aff.costs',string="Costo fijo")
    description = fields.Char(string="Descripcion", related='cost_id.description')
    template_id = fields.Many2one('aff.cost.template',string="Plantilla")
    form_type = fields.Selection(selection_forms, string="Forms")
    period = fields.Selection(selection_period, string="Periodo-tipo")
    estimated_amount = fields.Float(string="Monto Estimado")
    amount_made = fields.Float(string="Monto Realizado", compute="get_made_amount", store=True)
    airplane_id = fields.Many2one('aff.aircraf',string="Aeronave")

    ################ FORM 1  ########################################
    form1_amount = fields.Float(string="Monto1")

    ################ FORM 2  ########################################
    form2_amount = fields.Float(string="Monto 2", compute="total_amount_form2")
    pilot_payslip_ids = fields.One2many('cost.payslip.pilot','fixed_cost_id',string="Planilla tripulacion")

    ################ FORM 3  ########################################
    training_ids = fields.One2many('cost.training.crews','fixed_cost_id',string="Capacitaciones tripulacion")
    travel_expense_ids = fields.One2many('cost.travel.expense','fixed_cost_id',string="Viaticos tripulacion")
    qty_people = fields.Float(string="Num. Tripulaciones")
    total_1 = fields.Float(string="Total Capacitaciones", compute="total_amount_form3")
    total_2 = fields.Float(string="Total Viaticos", compute="total_amount_form3")
    total_anual_crews = fields.Float(string="Total Tripulaciones(Anual)", compute="total_amount_form3")
    form3_amount = fields.Float(string="Total Tripulaciones(Mensual", compute="total_amount_form3")

    ################ FORM 4  ########################################
    maintenance_line_ids = fields.One2many('cost.maintenance.line','fixed_cost_id',string="Lineas de Mantenimiento")
    hours_flown = fields.Float(string="Horas Voladas")
    cycles = fields.Float(string="Ciclos")
    ratio = fields.Float(string="Ratios")
    penalty = fields.Float(string="Penalidad")
    value_1 = fields.Float(string="0.24:1 or lower", tracking=True)
    value_2 = fields.Float(string="0.25:1 or 0.49:1", tracking=True)
    value_3 = fields.Float(string="0.50:1 or 0.74:1", tracking=True)
    value_4 = fields.Float(string="0.75:1 or 0.99:1", tracking=True)
    value_5 = fields.Float(string="1.0:1 or higher", tracking=True)
    form4_amount = fields.Float(string="Total reservas", compute="total_amount_form4")

    ################ FORM 5  ########################################
    form5_amount = fields.Float(string="Total Form 5")
    average_price = fields.Float(string="Precio Prom. Fuel")
    gallons_gassed = fields.Float(string="Galones Gaseados")
    reminder = fields.Float(string="Remanente")
    gallons_burned = fields.Float(string="Galones Quemados")
    bt = fields.Float(string="Horas Bloque (BT)")
    bt_gallons = fields.Float(string="Galones BT")
    fuel_price = fields.Float(string="Precio  Fuel x BT")

    ################ FORM 6  ########################################
    form6_amount = fields.Float(string="Monto 6", compute="total_amount_form6")
    crew_bonus_ids = fields.One2many('cost.crew.bonus','fixed_cost_id',string="Bonificaciones tripulacion")
    cycles = fields.Float(string="Ciclos")

    ################ FORM 8  ########################################
    form8_amount = fields.Float(string="Monto 6", compute="total_amount_form8")
    supplies_ids = fields.One2many('cost.supplies.line','fixed_cost_id',string="Suministros y Lubricantes")

    ################ FORM 10  ########################################
    form10_amount = fields.Float(string="Monto 10", compute="total_amount_form10")
    suppliers_ids = fields.One2many('cost.suppliers.line','fixed_cost_id',string="Proveedores")
    monthly_average = fields.Float(string="Promedio Mensual", compute="total_amount_form10")

    @api.depends('form1_amount','form2_amount','form3_amount','form4_amount','form5_amount','form6_amount','form8_amount','form10_amount','form_type')
    def get_made_amount(self):
        for rec in self:
            if rec.form_type == 'form01':
                rec.amount_made = rec.form1_amount
            elif rec.form_type == 'form02':
                rec.amount_made = rec.form2_amount
            elif rec.form_type == 'form03':
                rec.amount_made = rec.form3_amount
            elif rec.form_type == 'form04':
                rec.amount_made = rec.form4_amount
            elif rec.form_type == 'form05':
                rec.amount_made = rec.form5_amount
            elif rec.form_type == 'form06':
                rec.amount_made = rec.form6_amount
            elif rec.form_type == 'form08':
                rec.amount_made = rec.form8_amount
            elif rec.form_type == 'form10':
                rec.amount_made = rec.form10_amount
            else:
                rec.amount_made = 0


    @api.onchange('gallons_gassed','reminder','bt','average_price')
    def get_fuel_price(self):
        try:
            self.gallons_burned = self.gallons_gassed - self.reminder
            self.bt_gallons = self.gallons_burned / self.bt
            self.fuel_price = self.average_price * self.bt_gallons
            self.form5_amount =  self.fuel_price * self.bt
        except:
            self.gallons_burned = 0
            self.bt_gallons = 0
            self.fuel_price = 0
            self.form5_amount = 0

    @api.onchange('hours_flown','cycles')
    def get_ratio_penalty(self):
        if self.hours_flown > 0 and self.cycles > 0:
            self.ratio = self.hours_flown / self.cycles

            if self.ratio <= 0.24:
                self.penalty = self.value_1
            elif 0.25 <= self.ratio <= 0.49:
                self.penalty = self.value_2
            elif 0.50 <= self.ratio <= 0.74:
                self.penalty = self.value_3
            elif 0.75 <= self.ratio <= 0.99:
                self.penalty = self.value_4
            else:
                self.penalty = self.value_5

    @api.onchange('form_type', 'airplane_id')
    def form_type_change(self):
        if self.form_type == 'form04':
            self.value_1 = self.airplane_id.value_1
            self.value_2 = self.airplane_id.value_2
            self.value_3 = self.airplane_id.value_3
            self.value_4 = self.airplane_id.value_4
            self.value_5 = self.airplane_id.value_5

    @api.depends('pilot_payslip_ids')
    def total_amount_form2(self):
        for rec in self:
            if rec.form_type == 'form02' and len(rec.pilot_payslip_ids) > 0:
                rec.form2_amount = sum(rec.pilot_payslip_ids.mapped('total_monthly_trip'))
            else:
                rec.form2_amount = 0

    @api.depends('training_ids','travel_expense_ids')
    def total_amount_form3(self):
        for rec in self:
            total_training = 0
            total_expense_travel = 0
            if rec.form_type == 'form03':
                for training in rec.training_ids:
                    total_training += training.total

                for exp in rec.travel_expense_ids:
                    total_expense_travel += exp.total
            else:
                rec.form3_amount = 0
                rec.total_1 = 0
                rec.total_2 = 0
            rec.total_1 = total_training
            rec.total_2 = total_expense_travel
            rec.total_anual_crews = rec.total_1 + rec.total_2
            rec.form3_amount = rec.total_anual_crews / 24

    @api.depends('maintenance_line_ids')
    def total_amount_form4(self):
        for rec in self:
            if rec.form_type == 'form04' and len(rec.maintenance_line_ids) > 0:
                rec.form4_amount = sum(rec.maintenance_line_ids.mapped('monthly_total'))
            else:
                rec.form4_amount = 0
    
    @api.depends('crew_bonus_ids')
    def total_amount_form6(self):
        for rec in self:
            if rec.form_type == 'form06' and len(rec.crew_bonus_ids) > 0:
                rec.form6_amount = sum(rec.crew_bonus_ids.mapped('amount'))
            else:
                rec.form6_amount = 0

    @api.depends('supplies_ids')
    def total_amount_form8(self):
        for rec in self:
            if rec.form_type == 'form08' and len(rec.supplies_ids) > 0:
                rec.form8_amount = sum(rec.supplies_ids.mapped('total'))
            else:
                rec.form8_amount = 0

    @api.depends('suppliers_ids')
    def total_amount_form10(self):
        for rec in self:
            total_amount = 0
            average = 0
            count_line = 0
            if rec.form_type == 'form10' and len(rec.suppliers_ids) > 0:
                for line in rec.suppliers_ids:
                    total_amount += line.total
                    count_line += 1

            try:
                rec.monthly_average = total_amount/count_line
                rec.form10_amount = rec.monthly_average
            except:
                rec.monthly_average = 0
                rec.form10_amount = 0


class variableCostLines(models.Model):
    _name = 'variable.cost.lines'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Lineas de costo variable"

    line_id = fields.Many2one('aff.cost.sheets.lines',string="Linea de costo")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    year = fields.Char(string="Año")
    cost_id = fields.Many2one('aff.costs',string="Costo variable")
    description = fields.Char(string="Descripcion", related='cost_id.description')
    template_id = fields.Many2one(related='cost_id.template_id', string="Plantilla")
    form_type = fields.Selection(selection_forms, string="Forms")
    period = fields.Selection(selection_period, string="Periodo-tipo")
    estimated_amount = fields.Float(string="Monto Estimado")
    amount_made = fields.Float(string="Monto Realizado", compute="get_made_amount", store=True)
    airplane_id = fields.Many2one('aff.aircraf',string="Aeronave")

    ################ FORM 1  ########################################
    form1_amount = fields.Float(string="Monto1")

    ################ FORM 2  ########################################
    form2_amount = fields.Float(string="Monto 2", compute="total_amount_form2")
    pilot_payslip_ids = fields.One2many('cost.payslip.pilot','variable_cost_id',string="Planilla tripulacion")

    ################ FORM 3  ########################################
    training_ids = fields.One2many('cost.training.crews','variable_cost_id',string="Capacitaciones tripulacion")
    travel_expense_ids = fields.One2many('cost.travel.expense','variable_cost_id',string="Viaticos tripulacion")
    qty_people = fields.Float(string="Num. Tripulaciones")
    total_1 = fields.Float(string="Total Capacitaciones", compute="total_amount_form3")
    total_2 = fields.Float(string="Total Viaticos", compute="total_amount_form3")
    total_anual_crews = fields.Float(string="Total Tripulaciones(Anual)", compute="total_amount_form3")
    form3_amount = fields.Float(string="Total Tripulaciones(Mensual", compute="total_amount_form3")

    ################ FORM 4  ########################################
    maintenance_line_ids = fields.One2many('cost.maintenance.line','variable_cost_id',string="Lineas de Mantenimiento")
    hours_flown = fields.Float(string="Horas Voladas")
    cycles = fields.Float(string="Ciclos")
    ratio = fields.Float(string="Ratios")
    penalty = fields.Float(string="Penalidad")
    value_1 = fields.Float(string="0.24:1 or lower", tracking=True)
    value_2 = fields.Float(string="0.25:1 or 0.49:1", tracking=True)
    value_3 = fields.Float(string="0.50:1 or 0.74:1", tracking=True)
    value_4 = fields.Float(string="0.75:1 or 0.99:1", tracking=True)
    value_5 = fields.Float(string="1.0:1 or higher", tracking=True)
    form4_amount = fields.Float(string="Total reservas", compute="total_amount_form4")

    ################ FORM 5  ########################################
    form5_amount = fields.Float(string="Total Form 5")
    average_price = fields.Float(string="Precio Prom. Fuel")
    gallons_gassed = fields.Float(string="Galones Gaseados")
    reminder = fields.Float(string="Remanente")
    gallons_burned = fields.Float(string="Galones Quemados")
    bt = fields.Float(string="Horas Bloque (BT)")
    bt_gallons = fields.Float(string="Galones BT")
    fuel_price = fields.Float(string="Precio  Fuel x BT")

    ################ FORM 6  ########################################
    form6_amount = fields.Float(string="Monto 6", compute="total_amount_form6")
    crew_bonus_ids = fields.One2many('cost.crew.bonus','variable_cost_id',string="Bonificaciones tripulacion")
    cycles = fields.Float(string="Ciclos")

    ################ FORM 8  ########################################
    form8_amount = fields.Float(string="Monto 6", compute="total_amount_form8")
    supplies_ids = fields.One2many('cost.supplies.line','variable_cost_id',string="Suministros y Lubricantes")

    ################ FORM 10  ########################################
    form10_amount = fields.Float(string="Monto 10", compute="total_amount_form10")
    suppliers_ids = fields.One2many('cost.suppliers.line','variable_cost_id',string="Proveedores")
    monthly_average = fields.Float(string="Promedio Mensual", compute="total_amount_form10")

    @api.depends('form1_amount','form2_amount','form3_amount','form4_amount','form5_amount','form6_amount','form8_amount','form10_amount','form_type')
    def get_made_amount(self):
        for rec in self:
            if rec.form_type == 'form01':
                rec.amount_made = rec.form1_amount
            elif rec.form_type == 'form02':
                rec.amount_made = rec.form2_amount
            elif rec.form_type == 'form03':
                rec.amount_made = rec.form3_amount
            elif rec.form_type == 'form04':
                rec.amount_made = rec.form4_amount
            elif rec.form_type == 'form05':
                rec.amount_made = rec.form5_amount
            elif rec.form_type == 'form06':
                rec.amount_made = rec.form6_amount
            elif rec.form_type == 'form08':
                rec.amount_made = rec.form8_amount
            elif rec.form_type == 'form10':
                rec.amount_made = rec.form10_amount
            else:
                rec.amount_made = 0

    @api.onchange('gallons_gassed','reminder','bt','average_price')
    def get_fuel_price(self):
        try:
            self.gallons_burned = self.gallons_gassed - self.reminder
            self.bt_gallons = self.gallons_burned / self.bt
            self.fuel_price = self.average_price * self.bt_gallons
            self.form5_amount =  self.fuel_price * self.bt
        except:
            self.gallons_burned = 0
            self.bt_gallons = 0
            self.fuel_price = 0
            self.form5_amount = 0

    @api.onchange('hours_flown','cycles')
    def get_ratio_penalty(self):
        if self.hours_flown > 0 and self.cycles > 0:
            self.ratio = self.hours_flown / self.cycles

            if self.ratio <= 0.24:
                self.penalty = self.value_1
            elif 0.25 <= self.ratio <= 0.49:
                self.penalty = self.value_2
            elif 0.50 <= self.ratio <= 0.74:
                self.penalty = self.value_3
            elif 0.75 <= self.ratio <= 0.99:
                self.penalty = self.value_4
            else:
                self.penalty = self.value_5

    @api.onchange('form_type', 'airplane_id')
    def form_type_change(self):
        if self.form_type == 'form04':
            self.value_1 = self.airplane_id.value_1
            self.value_2 = self.airplane_id.value_2
            self.value_3 = self.airplane_id.value_3
            self.value_4 = self.airplane_id.value_4
            self.value_5 = self.airplane_id.value_5

    @api.depends('pilot_payslip_ids')
    def total_amount_form2(self):
        for rec in self:
            if rec.form_type == 'form02' and len(rec.pilot_payslip_ids) > 0:
                rec.form2_amount = sum(rec.pilot_payslip_ids.mapped('total_monthly_trip'))
            else:
                rec.form2_amount = 0

    @api.depends('training_ids','travel_expense_ids')
    def total_amount_form3(self):
        for rec in self:
            total_training = 0
            total_expense_travel = 0
            if rec.form_type == 'form03':
                for training in rec.training_ids:
                    total_training += training.total

                for exp in rec.travel_expense_ids:
                    total_expense_travel += exp.total
            else:
                rec.form3_amount = 0
                rec.total_1 = 0
                rec.total_2 = 0
            rec.total_1 = total_training
            rec.total_2 = total_expense_travel
            rec.total_anual_crews = rec.total_1 + rec.total_2
            rec.form3_amount = rec.total_anual_crews / 24

    @api.depends('maintenance_line_ids')
    def total_amount_form4(self):
        for rec in self:
            if rec.form_type == 'form04' and len(rec.maintenance_line_ids) > 0:
                rec.form4_amount = sum(rec.maintenance_line_ids.mapped('monthly_total'))
            else:
                rec.form4_amount = 0
    
    @api.depends('crew_bonus_ids')
    def total_amount_form6(self):
        for rec in self:
            if rec.form_type == 'form06' and len(rec.crew_bonus_ids) > 0:
                rec.form6_amount = sum(rec.crew_bonus_ids.mapped('amount'))
            else:
                rec.form6_amount = 0

    @api.depends('supplies_ids')
    def total_amount_form8(self):
        for rec in self:
            if rec.form_type == 'form08' and len(rec.supplies_ids) > 0:
                rec.form8_amount = sum(rec.supplies_ids.mapped('total'))
            else:
                rec.form8_amount = 0

    @api.depends('suppliers_ids')
    def total_amount_form10(self):
        for rec in self:
            total_amount = 0
            average = 0
            count_line = 0
            if rec.form_type == 'form10' and len(rec.suppliers_ids) > 0:
                for line in rec.suppliers_ids:
                    total_amount += line.total
                    count_line += 1

            try:
                rec.monthly_average = total_amount/count_line
                rec.form10_amount = rec.monthly_average
            except:
                rec.monthly_average = 0
                rec.form10_amount = 0
