# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

selection_forms = [
    ('form01', 'Form 1'),
    ('form02', 'Form 2')
]

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

    estimated_amount = fields.Float(string="Monto Estimado", compute="get_totals", store=True)
    amount_made = fields.Float(string="Monto Realizado", compute="get_totals", store=True)

    @api.depends('line_ids.estimated_amount', 'line_ids.amount_made')
    def get_totals(self):
        for rec in self:
            rec.estimated_amount = sum(rec.line_ids.mapped('estimated_amount'))
            rec.amount_made = sum(rec.line_ids.mapped('amount_made'))

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
                'start_date': self.initial_date,
                'final_date': self.final_date,
                'year': self.year
            }
            for fixed in fixed_cost_ids:
                estimated_amount, estimate_id = self.get_estimated_amount(self.initial_date, self.final_date, fixed, aircraf)
                line = {
                    'cost_id': fixed.id,
                    'airplane_id': aircraf.id,
                    'trimester': self.trimester,
                    'year': self.year,
                    'estimated_amount': estimated_amount,
                    'template_id': False,
                    'period': fixed.period,
                }

                if estimate_id:
                    print ("###############################")
                    print (estimate_id.cycles)
                    print (estimate_id.bt)
                    print (estimate_id.hours_flown)
                    print (estimate_id.ratio)
                    print (estimate_id.penalty)
                    values.update(
                        {
                        'cycles': estimate_id.cycles if estimate_id.cycles > 0 else 0,
                        'bt': estimate_id.bt if estimate_id.bt > 0 else 0,
                        'ft': estimate_id.hours_flown if estimate_id.hours_flown > 0 else 0,
                        'ratio': estimate_id.ratio if estimate_id.ratio > 0 else 0,
                        'penalty': estimate_id.penalty if estimate_id.penalty > 0 else 0,
                        }
                    )
                    line = self.get_data_estimated(estimate_id, line)

                fixed_cost.append((0,0,line))

            for variable in variable_cost_ids:
                estimated_amount, estimate_id = self.get_estimated_amount(self.initial_date, self.final_date, variable, aircraf)
                line = {
                    'cost_id': variable.id,
                    'trimester': self.trimester,
                    'year': self.year,
                    'estimated_amount': estimated_amount,
                    'period': variable.period
                }

                if estimate_id:
                    values.update(
                        {
                        'cycles': estimate_id.cycles if estimate_id.cycles > 0 else 0,
                        'bt': estimate_id.bt if estimate_id.bt > 0 else 0,
                        'ft': estimate_id.hours_flown if estimate_id.hours_flown > 0 else 0,
                        'ratio': estimate_id.ratio if estimate_id.ratio > 0 else 0,
                        'penalty': estimate_id.penalty if estimate_id.penalty > 0 else 0,
                        }
                    )
                    line = self.get_data_estimated(estimate_id, line)

                variable_cost.append((0,0,line))

            if fixed_cost:
                values.update({'fixed_cost_ids': fixed_cost})

            if variable_cost:
                values.update({'variable_cost_ids': variable_cost})

            self.env['aff.cost.sheets.lines'].create(values)

    def get_data_estimated(self, estimate_id, line):
        line.update({
            'form_type': estimate_id.form_type,
            'template_id': estimate_id.id,

            ################ FORM 1  ######################
            'form1_amount': estimate_id.form1_amount,

            ################ FORM 3  ######################
            'qty_people': estimate_id.qty_people,

            ################ FORM 4  ######################
            'hours_flown': estimate_id.hours_flown,
            'cycles': estimate_id.cycles,
            'ratio': estimate_id.ratio,
            'penalty': estimate_id.penalty,
            'value_1': estimate_id.value_1,
            'value_2': estimate_id.value_2,
            'value_3': estimate_id.value_3,
            'value_4': estimate_id.value_4,
            'value_5': estimate_id.value_5,

            ################ FORM 5  ######################
            'form5_amount': estimate_id.form5_amount,
            'average_price': estimate_id.average_price,
            'gallons_gassed': estimate_id.gallons_gassed,
            'reminder': estimate_id.reminder,
            'gallons_burned': estimate_id.gallons_burned,
            'bt': estimate_id.bt,
            'bt_gallons': estimate_id.bt_gallons,
            'fuel_price': estimate_id.fuel_price,
        })

        # FORM 2
        pilot_payslip_lines = []

        for payslip in estimate_id.pilot_payslip_ids:
            pilot_payslip_lines.append((0, 0, {
                # aquí los campos que existan en cost.payslip.pilot
                'qty': payslip.qty,
                'position': payslip.position,
                'salary': payslip.salary,
                'monthly_trip': payslip.monthly_trip,
                'crews': payslip.crews,
                'total_monthly_trip': payslip.total_monthly_trip
                # ...
            }))

        line['pilot_payslip_ids'] = pilot_payslip_lines

        # FORM 3 - CAPACITACIONES
        training_lines = []

        for training in estimate_id.training_ids:
            training_lines.append((0, 0, {
                # campos de cost.training.crews
                'training_id': training.training_id.id,
                'cost': training.cost,
                'first_year': training.first_year,
                'second_year': training.second_year,
                'total': training.total,
                'qty_people': training.qty_people,
                'people': training.people,
                'unit_cost': training.unit_cost,
                # ...
            }))

        line['training_ids'] = training_lines

        # FORM 3 - VIÁTICOS
        travel_lines = []

        for travel in estimate_id.travel_expense_ids:
            travel_lines.append((0, 0, {
                # campos de cost.travel.expense
                'travel_expense': travel.travel_expense,
                'days1': travel.days1,
                'days2': travel.days2,
                'assignment': travel.assignment,
                'total': travel.total,
                'first_year': travel.first_year,
                'second_year': travel.second_year,
                'total': travel.total,
                'qty_people': travel.qty_people
                # ...
            }))

        line['travel_expense_ids'] = travel_lines

        # FORM 4 - MANTENIMIENTO
        maintenance_lines = []

        for maintenance in estimate_id.maintenance_line_ids:
            maintenance_lines.append((0, 0, {
                # campos de cost.maintenance.line
                'reservation_id': maintenance.reservation_id.id,
                'hourly_reservation': maintenance.hourly_reservation,
                'monthly_total': maintenance.monthly_total,
                'hours_flown': maintenance.hours_flown,
                'cycles': maintenance.cycles,
                'ratio': maintenance.ratio,
                'penalty': maintenance.penalty
                # ...
            }))

        line['maintenance_line_ids'] = maintenance_lines

        # FORM 6 - BONIFICACIONES
        bonus_lines = []

        for bonus in estimate_id.crew_bonus_ids:
            bonus_lines.append((0, 0, {
                # campos de cost.crew.bonus
                'employee_id': bonus.employee_id.id,
                'amount': bonus.amount,
                # ...
            }))

        line['crew_bonus_ids'] = bonus_lines

        # FORM 8 - SUMINISTROS
        supplies_lines = []

        for supply in estimate_id.supplies_ids:
            supplies_lines.append((0, 0, {
                # campos de cost.supplies.line
                'product_id': supply.product_id.id,
                'quantity': supply.quantity,
                'amount': supply.amount,
                # ...
            }))

        line['supplies_ids'] = supplies_lines

        # FORM 10 - PROVEEDORES
        supplier_lines = []

        for supplier in estimate_id.suppliers_ids:
            supplier_lines.append((0, 0, {
                # campos de cost.suppliers.line
                'partner_id': supplier.partner_id.id,
                'amount': supplier.amount,
                # ...
            }))

        line['suppliers_ids'] = supplier_lines

        return line

    def get_estimated_amount(self, initial_date, final_date, rec_id, airplane):
        amount = 0
        estimated_id = self.env['aff.cost.template'].search([('state','=','validated'),('cost_id','=',rec_id.id),('initial_date','<=',initial_date),('final_date','>=',final_date),('airplane_ids','in',[airplane.id])])
        if estimated_id:
            if estimated_id.estimation_type == 'dynamic':
                if estimated_id.form_type == 'form01':
                    amount = estimated_id.form1_amount
                elif estimated_id.form_type == 'form02':
                    amount = estimated_id.form2_amount
                elif estimated_id.form_type == 'form03':
                    amount = estimated_id.form3_amount
                elif estimated_id.form_type == 'form04':
                    amount = estimated_id.form4_amount
                elif estimated_id.form_type == 'form05':
                    amount = estimated_id.form5_amount
                elif estimated_id.form_type == 'form06':
                    amount = estimated_id.form6_amount
                elif estimated_id.form_type == 'form07':
                    amount = estimated_id.form7_amount
                elif estimated_id.form_type == 'form08':
                    amount = estimated_id.form8_amount
                elif estimated_id.form_type == 'form09':
                    amount = estimated_id.form9_amount
                else:
                    amount = estimated_id.form10_amount
            else:
                line_id = estimated_id.distribution_line_ids.filtered(lambda line: line.initial_date <= initial_date and line.final_date >= final_date)
                if line_id:
                    amount = line_id.amount
        
        return amount, estimated_id


class costSheetsLines(models.Model):
    _name = 'aff.cost.sheets.lines'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Lineas hoja de costos"

    sheet_id = fields.Many2one('aff.cost.sheets',string="Hoja de costo")
    period = fields.Selection([('annual','Anual'),('monthly','Mensual'),('useful_life','Vida Util')], string="Periodo-Tipo", default="annual")
    trimester = fields.Selection([('1', '1er Trimestre'),('2', '2do Trimestre'),('3', '3er Trimestre'),('4', '4to Trimestre')],string="Trimestre")
    aircraft_id = fields.Many2one('aff.aircraf',string="Aeronave")
    year = fields.Char(string="Año")
    form_type = fields.Selection(selection_forms, string="Forms")
    fixed_cost_ids = fields.One2many('fixed.cost.lines','line_id',string="Costos Fijos")
    variable_cost_ids = fields.One2many('variable.cost.lines','line_id',string="Costos Variables")

    estimated_amount = fields.Float(string="Monto Estimado", compute="get_totals", store=True)
    amount_made = fields.Float(string="Monto Realizado", compute="get_totals", store=True)

    start_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha Final")
    months_duration = fields.Float(string="Duracion(Meses)")

    cycles = fields.Float(string="Ciclos")
    bt = fields.Float(string="Horas Bloque (BT)")
    ft = fields.Float(string="Horas Vuelo (FT)")
    ratio = fields.Float(string="Ratios")
    penalty = fields.Float(string="Penalidad")

    real_cycles = fields.Float(string="Ciclos real")
    real_bt = fields.Float(string="Horas Bloque (BT) real")
    real_ft = fields.Float(string="Horas Vuelo (FT) real")
    real_ratio = fields.Float(string="Ratios real")
    real_penalty = fields.Float(string="Penalidad real")

    update_data = fields.Boolean(string="Actualizar datos")

    @api.onchange('real_cycles','real_bt','real_ft','real_ratio','real_penalty')
    def _onchange_datas(self):
        self.update_data = True

    def update_lines(self):
        self.update_data = False
        for line in self.fixed_cost_ids:
            line.cycles = self.real_cycles
            line.bt = self.real_bt
            line.hours_flown = self.real_ft
            line.ratio = self.real_ratio
            line.penalty = self.real_penalty
            line.get_made_amount()
            line.get_fuel_price()
            line.get_ratio_penalty()
            line.form_type_change()
            line.total_amount_form2()
            line.total_amount_form3()
            line.total_amount_form4()
            line.total_amount_form6()
            line.total_amount_form8()
            line.total_amount_form10()

        for line in self.variable_cost_ids:
            line.cycles = self.real_cycles
            line.bt = self.real_bt
            line.hours_flown = self.real_ft
            line.ratio = self.real_ratio
            line.penalty = self.real_penalty
            line.get_made_amount()
            line.get_fuel_price()
            line.get_ratio_penalty()
            line.form_type_change()
            line.total_amount_form2()
            line.total_amount_form3()
            line.total_amount_form4()
            line.total_amount_form6()
            line.total_amount_form8()
            line.total_amount_form10()
        return True

    @api.depends('fixed_cost_ids.estimated_amount', 'variable_cost_ids.estimated_amount', 'fixed_cost_ids.amount_made', 'variable_cost_ids.amount_made')
    def get_totals(self):
        for rec in self:
            rec.estimated_amount = sum(rec.fixed_cost_ids.mapped('estimated_amount')) + sum(rec.variable_cost_ids.mapped('estimated_amount'))
            rec.amount_made = sum(rec.fixed_cost_ids.mapped('amount_made')) + sum(rec.variable_cost_ids.mapped('amount_made'))