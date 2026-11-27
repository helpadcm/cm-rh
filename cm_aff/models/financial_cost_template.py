from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from odoo.exceptions import ValidationError

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

selection_period = [
    ('annual', 'Anual'),
    ('monthly', 'Mensual'),
    ('useful_life', 'Vida Util')
]

class AffCostTemplate(models.Model):
    _name = 'aff.cost.template'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Cedulas de estimacion'

    name = fields.Char(string='Nombre de la Plantilla', required=True)
    initial_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha Final")
    form_type = fields.Selection(selection_forms, string="Forms")
    state = fields.Selection([('draft','Borrador'),('validated','Validado'),('finalized','Finalizado')], string="Estado", default="draft")
    cost_id = fields.Many2one('aff.costs',string="Rubro")
    period = fields.Selection(selection_period, string="Periodo-tipo",default="monthly")
    sequence = fields.Integer(string="Secuencia")
    distribution_line_ids = fields.One2many('cost.monthly.distribution','estimate_id',string="Distribucion mensual")
    duration_months = fields.Float(string="Duracion Meses")
    estimation_type = fields.Selection([('constant','Constante'),('dynamic','Dinamico')],string="Tipo de Cedula",default="dynamic",tracking=True)
    airplane_ids = fields.Many2many('aff.aircraf',string="Aeronaves")

    ################ FORM 1  ########################################
    form1_amount = fields.Float(string="Monto")

    ################ FORM 2  ########################################
    form2_amount = fields.Float(string="Monto 2", compute="total_amount_form2")
    pilot_payslip_ids = fields.One2many('cost.payslip.pilot','estimate_id',string="Planilla tripulacion")

    ################ FORM 3  ########################################
    training_ids = fields.One2many('cost.training.crews','estimate_id',string="Capacitaciones tripulacion")
    travel_expense_ids = fields.One2many('cost.travel.expense','estimate_id',string="Viaticos tripulacion")
    qty_people = fields.Float(string="Num. Tripulaciones")
    total_1 = fields.Float(string="Total Capacitaciones", compute="total_amount_form3")
    total_2 = fields.Float(string="Total Viaticos", compute="total_amount_form3")
    total_anual_crews = fields.Float(string="Total Tripulaciones(Anual)", compute="total_amount_form3")
    form3_amount = fields.Float(string="Total Tripulaciones(Mensual", compute="total_amount_form3")

    ################ FORM 4  ########################################
    maintenance_line_ids = fields.One2many('cost.maintenance.line','estimate_id',string="Lineas de Mantenimiento")
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
    crew_bonus_ids = fields.One2many('cost.crew.bonus','estimate_id',string="Bonificaciones tripulacion")
    cycles = fields.Float(string="Ciclos")

    ################ FORM 8  ########################################
    form8_amount = fields.Float(string="Monto 6", compute="total_amount_form8")
    supplies_ids = fields.One2many('cost.supplies.line','estimate_id',string="Suministros y Lubricantes")

    ################ FORM 10  ########################################
    form10_amount = fields.Float(string="Monto 10", compute="total_amount_form10")
    suppliers_ids = fields.One2many('cost.suppliers.line','estimate_id',string="Proveedores")
    monthly_average = fields.Float(string="Promedio Mensual", compute="total_amount_form10")

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

    @api.onchange('form_type', 'airplane_ids')
    def form_type_change(self):
        if self.form_type == 'form04':
            if len(self.airplane_ids) > 1:
                raise ValidationError("Para el Form 4 se debe seleccionar una sola aeronave.")

            if len(self.airplane_ids) == 1:
                self.value_1 = self.airplane_ids[0].value_1
                self.value_2 = self.airplane_ids[0].value_2
                self.value_3 = self.airplane_ids[0].value_3
                self.value_4 = self.airplane_ids[0].value_4
                self.value_5 = self.airplane_ids[0].value_5


    def validate(self):
        self.state = 'validated'

    def set_to_draft(self):
        self.state = 'draft'

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

    @api.depends('suppliers_ids','airplane_ids')
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
                if rec.airplane_ids:
                    rec.form10_amount = rec.monthly_average/len(rec.airplane_ids)
                else:
                    rec.form10_amount = 0
            except:
                rec.monthly_average = 0
                rec.form10_amount = 0

    @api.onchange('initial_date', 'final_date')
    def calculate_durations(self):
        if self.initial_date and self.final_date:
            difference = relativedelta(self.final_date, self.initial_date)
            months = difference.years * 12 + difference.months
            self.duration_months = months

    def create_distribution(self):
        for record in self:
            if not record.initial_date or not record.final_date:
                continue

            if record.initial_date > record.final_date:
                raise ValidationError(
                    "La fecha inicial no puede ser mayor que la fecha final."
                )

            # Eliminar distribución anterior
            record.distribution_line_ids.unlink()

            lines = []

            current_date = record.initial_date
            month_number = 1

            if record.form_type == 'form01':
                amount = record.form1_amount
            elif record.form_type == 'form02':
                amount = record.form2_amount
            elif record.form_type == 'form03':
                amount = record.form3_amount
            elif record.form_type == 'form04':
                amount = record.form4_amount
            elif record.form_type == 'form06':
                amount = record.form6_amount
            else:
                amount = 0

            if record.period == 'annual':
                amount = amount / 12
            elif record.period == 'useful_life':
                amount = amount / record.duration_months

            while current_date < record.final_date:

                # Último día del mes actual
                last_day = monthrange(
                    current_date.year,
                    current_date.month
                )[1]

                current_month_end = current_date.replace(
                    day=last_day
                )

                # No permitir que la fecha final de la línea
                # sea mayor que la fecha final de la plantilla
                line_final_date = min(
                    current_month_end,
                    record.final_date
                )

                lines.append({
                    'name': f'Mes {month_number}',
                    'initial_date': current_date,
                    'final_date': line_final_date,
                    'amount': amount,
                    'estimate_id': record.id,
                })

                # Pasar al primer día del siguiente mes
                current_date = (
                    current_date + relativedelta(months=1)
                ).replace(day=1)

                month_number += 1

            self.env['cost.monthly.distribution'].create(lines)

class monthlyDistribution(models.Model):
    _name = 'cost.monthly.distribution'
    _description = "Distribuciones mensuales"

    name = fields.Char(string="Mes")
    initial_date = fields.Date(string="Fecha Inicio")
    final_date = fields.Date(string="Fecha Final")
    amount = fields.Float(string="Monto")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

class pilotPayslip(models.Model):
    _name = 'cost.payslip.pilot'
    _description = "Remuneracion de tripulaciones"

    qty = fields.Char(string="Cantidad")
    position = fields.Char(string="Puesto")
    salary = fields.Float(string="Salario Nominal")
    monthly_trip = fields.Float(string="Mensual 1 Trip.")
    crews = fields.Integer(string="Tripulaciones")
    total_monthly_trip = fields.Float(string="Mensual Total Trip.")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('salary','crews')
    def get_amounts(self):
        self.monthly_trip = self.salary * 1.25
        self.total_monthly_trip = self.monthly_trip * self.crews

class crewBonus(models.Model):
    _name = 'cost.crew.bonus'
    _description = "Bonus de tripulaciones"

    position = fields.Char(string="Puesto")
    min_sectors = fields.Float(string="Min Sectores")
    sector_bonus = fields.Float(string="Bono x Sector")
    crew_qty = fields.Integer(string="Cant. Tripulaciones")
    qty_sectors = fields.Integer(string="Cant. Sectores")
    sectors_carried = fields.Integer(string="Sectores Realizados")
    bonus = fields.Integer(string="Bonificables")
    amount = fields.Float(string="Calculo")
    cycles = fields.Float(string="Ciclos")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('min_sectors','crew_qty','cycles','sector_bonus')
    def get_amounts(self):
        self.qty_sectors = self.min_sectors * self.crew_qty
        self.sectors_carried = self.cycles
        self.bonus = self.sectors_carried - self.qty_sectors
        self.amount = self.bonus * self.sector_bonus

class trainingCreww(models.Model):
    _name = 'cost.training.crews'
    _description = "Capacitaciones tripulacion"

    training_id = fields.Many2one('aff.trainings',string="Capacitaciones")
    cost = fields.Float(string="Costo")
    first_year = fields.Float(string="Primer Año")
    second_year = fields.Float(string="Segundo Año")
    total = fields.Float(string="Total")
    qty_people = fields.Float(string="Num. Tripulaciones")
    people = fields.Float(string="Num. Personas")
    unit_cost = fields.Float(string="Costo Unitario")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('unit_cost')
    def get_amounts_cost(self):
        if self.unit_cost > 0:
            self.cost = self.unit_cost * self.people

    @api.onchange('cost','training_id','people','unit_cost','qty_people')
    def get_amounts(self):
        if self.training_id.apply_to == 'first_year':
            self.first_year = self.cost * self.qty_people
            self.second_year = 0
        elif self.training_id.apply_to == 'second_year':
            self.second_year = self.cost * self.qty_people
            self.first_year = 0
        else:
            self.first_year = self.cost * self.qty_people
            self.second_year = self.cost * self.qty_people

        self.total = self.first_year + self.second_year

class travelExpenses(models.Model):
    _name = 'cost.travel.expense'
    _description = "Viaticos tripulacion"

    travel_expense = fields.Selection([
        ('op1','Boletos Aereos'),
        ('op2','Viaticos Inicial'),
        ('op3','Viaticos Recurrente'),
        ('op4','Viaticos PC'),
        ('op5','Hotel'),
        ('op6','Transporte')],string="Viatico")
    days1 = fields.Integer(string="Dias 1er Año")
    days2 = fields.Integer(string="Dias 2do Año")
    assignment = fields.Float(string="Asignacion")
    total = fields.Float(string="Total")
    first_year = fields.Float(string="Primer Año")
    second_year = fields.Float(string="Segundo Año")
    total = fields.Float(string="Total")
    qty_people = fields.Float(string="Num. Tripulaciones")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    # @api.onchange('unit_cost')
    # def get_amounts_cost(self):
    #     if self.unit_cost > 0:
    #         self.cost = self.unit_cost * self.people

    @api.onchange('travel_expense','days1','days2','assignment','qty_people')
    def get_amounts(self):
        self.first_year = self.qty_people * self.days1 * self.assignment
        self.second_year = self.qty_people * self.days2 * self.assignment

        if self.travel_expense == 'op1':
            self.total = self.qty_people * self.assignment
        else:
            self.total = self.first_year + self.second_year

class maintenanceLine(models.Model):
    _name = 'cost.maintenance.line'
    _description = "Lineas de mantenimiento"

    reservation_id = fields.Many2one('aff.reservations',string="Reserva")
    hourly_reservation = fields.Float(string="Reserva por hora")
    monthly_total = fields.Float(string="Total Mensual")
    hours_flown = fields.Float(string="Horas Voladas")
    cycles = fields.Float(string="Ciclos")
    ratio = fields.Float(string="Ratios")
    penalty = fields.Float(string="Penalidad")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('reservation_id','hourly_reservation')
    def get_amounts(self):
        if self.reservation_id:
            calculate_type = self.reservation_id.calculate_type
            amount = 0
            if calculate_type == 'fixed':
                amount = self.hourly_reservation
            elif calculate_type == 'cycles':
                amount = self.hourly_reservation * self.cycles
            elif calculate_type == 'hours':
                amount = self.hourly_reservation * self.hours_flown

            if self.reservation_id.penalty_applies:
                amount = amount * (self.penalty/100)

            self.monthly_total = amount

class suppliesLine(models.Model):
    _name = 'cost.supplies.line'
    _description = "Lineas de Suministros"

    supplie_id = fields.Many2one('aff.supplies',string="Reserva")
    cost = fields.Float(string="Costo")
    qty = fields.Integer(string="QTY")
    total = fields.Float(string="Total")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('cost', 'supplie_id', 'qty')
    def get_amounts(self):
        if self.supplie_id.amount > 0:
            self.cost = self.supplie_id.amount

        self.total = self.cost * self.qty

class suppliesLine(models.Model):
    _name = 'cost.suppliers.line'
    _description = "Lineas de proveedores"

    supplier_id = fields.Many2one('aff.suppliers',string="Proveedor")
    amount__month1 = fields.Float(string="Mes 1")
    amount__month2 = fields.Float(string="Mes 2")
    amount__month3 = fields.Float(string="Mes 3")
    amount__month4 = fields.Float(string="Mes 4")
    amount__month5 = fields.Float(string="Mes 5")
    amount__month6 = fields.Float(string="Mes 6")
    total = fields.Float(string="Total")
    estimate_id = fields.Many2one('aff.cost.template',string="Estimacion")
    fixed_cost_id = fields.Many2one('fixed.cost.lines',string="Costo Fijo")
    variable_cost_id = fields.Many2one('variable.cost.lines',string="Costo Variable")

    @api.onchange('amount__month1', 'amount__month2', 'amount__month3','amount__month4','amount__month5','amount__month6')
    def get_amounts(self):
        self.total = self.amount__month1 + self.amount__month2 + self.amount__month3 + self.amount__month4 + self.amount__month5 + self.amount__month6