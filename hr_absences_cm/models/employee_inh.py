from odoo import fields, models, api
from datetime import datetime

class HrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    compensatory_hours = fields.Float(string="Horas compensatorios Disp.")
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Float(string="Vacaciones Disp.",compute="get_available_vacations")
    early_vacations = fields.Float(string="Vacaciones Adelantadas")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")
    first_year = fields.Boolean(string="1er Año")
    second_year = fields.Boolean(string="2do Año")
    vacation_details_ids = fields.One2many('vacations.detail.list','employee_id',string="Detalle de vacaciones")

    @api.depends('vacation_details_ids','early_vacations')
    def get_available_vacations(self):
        for rec in self:
            vac_available = sum(rec.vacation_details_ids.mapped('pending_days'))
            rec.vacations_day = vac_available - rec.early_vacations

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 8
                days = int(rec.compensatory_hours // 8)
                hours = round((rec.compensatory_hours % 8), 2)
                rec.compensatory_day_string = f"{days} dia(s) y {hours} hora(s)"
            else:
                rec.compensatory_day = 0
                rec.compensatory_day_string = 'No disponibles'

    def update_personal_time(self):
        actual_date = datetime.now().date()
        for rec in self.search([]):
            if rec.date_start_contract:
                contract_date = rec.date_start_contract
                antique = int((actual_date - contract_date).days / 365)
                tickets = 0
                if antique == 1 and not rec.first_year:
                    tickets = 2
                    rec.first_year = True
                    self.create_vacations(rec,antique)
                elif antique == 2 and not rec.second_year:
                    tickets = 3
                    rec.second_year = True
                    self.create_vacations(rec,antique)
                elif antique >= 3:
                    tickets = 4
                    rec.second_year = True
                    rec.first_year = True
                    self.create_vacations(rec,antique)
                
                rec.program_to_fly = tickets

    def create_vacations(self, employee_id, years):
        days_qty = 0
        if years == 1:
            days_qty = 10
        elif years == 2:
            days_qty = 12
        elif years == 3:
            days_qty = 15
        elif years >= 4:
            days_qty = 20
        
        if days_qty > 0:
            vals = {
                'name': 'Vacaciones %s año(s)'%(years),
                'employee_id': employee_id.id,
                'assigned_days': days_qty,
                'pending_days': days_qty
            }
            if len(employee_id.vacation_details_ids) in [0,1]:
                employee_id.env['vacations.detail.list'].create(vals)
            elif len(employee_id.vacation_details_ids) == 2:
                employee_id.vacation_details_ids[0].unlink()
                employee_id.env['vacations.detail.list'].create(vals)

    def assign_vacations(self):
        actual_date = datetime.now().date()
        if self.date_start_contract:
            contract_date = self.date_start_contract
            years = int((actual_date - contract_date).days / 365)
            days_qty = 0
            
            for year in range(1,years+1):
                if year == 1:
                    days_qty = 10
                elif year == 2:
                    days_qty = 12
                elif year == 3:
                    days_qty = 15
                elif year >= 4:
                    days_qty = 20
                vals = {
                    'name': 'Vacaciones %s año(s)'%(year),
                    'employee_id': self.id,
                    'assigned_days': days_qty,
                    'pending_days': days_qty
                }
                if year in [1,2]:
                    if len(self.vacation_details_ids) in [0,1]:
                        self.env['vacations.detail.list'].create(vals)
                elif year >= 3:
                    if len(self.vacation_details_ids) == 2:
                        self.vacation_details_ids[0].unlink()
                        self.env['vacations.detail.list'].create(vals)

class employeePublicHRInh(models.Model):
    _inherit = 'hr.employee.public'

    compensatory_hours = fields.Float(string="Dias compensatorios Disp.")
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Integer(string="Vacaciones Disp.")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")
    first_year = fields.Boolean(string="1er Año")
    second_year = fields.Boolean(string="2do Año")

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 8
                days = int(rec.compensatory_hours // 8)
                hours = round((rec.compensatory_hours % 8), 2)
                rec.compensatory_day_string = f"{days} dias y {hours} horas"
            else:
                rec.compensatory_day = 0
                rec.compensatory_day_string = ''

class vacationsDetail(models.Model):
    _name = 'vacations.detail.list'
    _description = 'Detalle de vacaciones'

    name = fields.Char(string="Tiempo")
    assigned_days = fields.Integer(string="Dias Asignados")
    pending_days = fields.Float(string="Dias Pendientes")
    employee_id = fields.Many2one('hr.employee',string="Empleado")