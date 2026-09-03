from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

relationship_list = [
    ('mother', 'Madre'), ('father','Padre'),
    ('children','Hijo(a)'), ('siblings','Hermano(a)'),
    ('couple','Pareja'),('other','Otro'), ('employee','Empleado')
]

class HrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    compensatory_hours = fields.Float(string="Horas compensatorios Disp.",tracking=True)
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Float(string="Vacaciones Disp.",compute="get_available_vacations")
    early_vacations = fields.Float(string="Vacaciones Adelantadas",tracking=True)
    program_to_fly = fields.Float(string="Programa a Volar Disp.",tracking=True)
    first_year = fields.Boolean(string="1er Año")
    second_year = fields.Boolean(string="2do Año")
    vacation_details_ids = fields.One2many('vacations.detail.list','employee_id',string="Detalle de vacaciones")
    beneficiaries_ids = fields.One2many('beneficiaries.detail.list','employee_id',string="Beneficiarios")
    aeronatical_license = fields.Boolean(string="Posee Licencia Aeronautica",tracking=True)
    expiration_date_license = fields.Date(string="Fecha de vencimiento",tracking=True)
    license_number = fields.Char(string="Número de Licencia",tracking=True)
    license_type = fields.Selection([('pilot','Piloto'),('cabin_crew','Tripulante de Cabina'),('flight_dispatcher','Despachador de Vuelos'),('maintenance','Tecnico de Mantenimiento')],string="Tipo de Licencia",tracking=True)
    years_old = fields.Integer(string="Años de antiguedad")

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

    def _get_contract_years(self, contract_date, actual_date=None):
        """Devuelve los años completos de antigüedad."""
        actual_date = actual_date or datetime.now().date()

        if not contract_date or actual_date < contract_date:
            return 0

        return relativedelta(actual_date, contract_date).years

    def _get_vacation_days(self, years, has_aeronautical_license=False):
        """Devuelve los días de vacaciones correspondientes."""
        
        if has_aeronautical_license:
            return 30

        vacation_days = {
            1: 10,
            2: 12,
            3: 15,
        }

        return vacation_days.get(years, 20) if years >= 1 else 0

    def _create_vacation(self, employee, year):
        """Crea el período de vacaciones manteniendo máximo 2 períodos acumulados."""

        vacation_obj = self.env['vacations.detail.list']

        # Verificar si ya existe este año
        existing = employee.vacation_details_ids.filtered(
            lambda line: line.year == year
        )

        if existing:
            return

        # Obtener los períodos actuales
        vacations = employee.vacation_details_ids.sorted(
            key=lambda line: line.year
        )

        # Si ya tiene 2 períodos, eliminar el más antiguo
        if len(vacations) >= 2:
            oldest = vacations[0]
            oldest.unlink()

        assigned_days = self._get_vacation_days(
            year,
            employee.aeronatical_license
        )

        if assigned_days <= 0:
            return

        # Calcular días pendientes
        pending_days = assigned_days

        if employee.early_vacations > 0:
            pending_days = max(
                assigned_days - employee.early_vacations,
                0
            )

            employee.early_vacations = 0

        vacation_obj.create({
            'name': f'Vacaciones {year} año(s)',
            'employee_id': employee.id,
            'assigned_days': assigned_days,
            'pending_days': pending_days,
            'year': year,
        })

    def update_personal_time(self):
        actual_date = datetime.now().date()

        employees = self.search([('contract_date_start', '!=', False)])
        tickets_qty = 0

        for employee in employees:

            contract_date = employee.contract_date_start

            # Años completos de antigüedad
            years = self._get_contract_years(contract_date,actual_date)

            # Actualizar antigüedad
            employee.years_old = years

            # Menos de un año
            if years < 1:
                employee.program_to_fly = 0
                continue

            # Beneficio de boletos

            # Fecha exacta del aniversario
            anniversary = contract_date + relativedelta(
                years=years
            )

            # Solo asignar vacaciones el día del aniversario

            if actual_date == anniversary:
                if years == 1:
                    tickets_qty = 2
                elif years == 2:
                    tickets_qty = 3
                else:
                    tickets_qty = 4
                    
                self._create_vacation(employee,years)
                employee.program_to_fly = tickets_qty

class employeePublicHRInh(models.Model):
    _inherit = 'hr.employee.public'

    compensatory_hours = fields.Float(string="Dias compensatorios Disp.")
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Float(string="Vacaciones Disp.",compute="get_available_vacations")
    early_vacations = fields.Float(string="Vacaciones Adelantadas")
    program_to_fly = fields.Float(string="Programa a Volar Disp.")
    first_year = fields.Boolean(string="1er Año")
    second_year = fields.Boolean(string="2do Año")
    vacation_details_ids = fields.One2many('vacations.detail.list','employee_id',string="Detalle de vacaciones")
    beneficiaries_ids = fields.One2many('beneficiaries.detail.list','employee_id',string="Beneficiarios")
    aeronatical_license = fields.Boolean(string="Posee Licencia Aeronautica")
    expiration_date_license = fields.Date(string="Fecha de vencimiento")
    license_type = fields.Selection([('pilot','Piloto'),('cabin_crew','Tripulante de Cabina'),('flight_dispatcher','Despachador de Vuelos'),('maintenance','Tecnico de Mantenimiento')],string="Tipo de Licencia")
    years_old = fields.Integer(string="Años de antiguedad")

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
    year = fields.Integer(string="Año")

class beneficiariesDetail(models.Model):
    _name = 'beneficiaries.detail.list'
    _description = 'Beneficiarios programa a volar'

    employee_id = fields.Many2one('hr.employee',string="Empleado")
    name = fields.Char(string="Nombre")
    identity = fields.Char(string="Identidad")
    birthday = fields.Date(string="Fecha de nacimiento")
    relationship = fields.Selection(relationship_list ,string="Parentesto")
    observation = fields.Char(string="Observaciones")
    is_employee = fields.Boolean(string="Es empleado")