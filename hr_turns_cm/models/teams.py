from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class workTeams(models.Model):
    _name = 'hr.work.teams'
    _description = 'Teams: Work teams'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Name',tracking=True)
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo",tracking=True)
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo",tracking=True)
    active = fields.Boolean(string="Activo", default=True,tracking=True)
    member_employees_ids = fields.One2many('hr.employees.members','team_id',string="Miembros de equipo")

class membersEmployee(models.Model):
    _name = 'hr.employees.members'
    _description = 'Lista Miembros: Miembros de equipo'

    employee_id = fields.Many2one('hr.employee',string="Empleado")
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    department_id = fields.Many2one('hr.department', string="Departamento")
    job_id = fields.Many2one('hr.job', string="Puesto de Trabajo")
    template_id = fields.Many2one('hr.templates.turn',string="Turno")

    @api.onchange('employee_id')
    def get_data_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id

class optionsSchedule(models.Model):
    _name = 'hr.options.schedules'
    _description = 'Horarios: horarios disponibles para los turnos'

    name = fields.Char(string="Nombre")
    alphabetical = fields.Boolean(string="Alfabetico")

class turnTypes(models.Model):
    _name = 'hr.turn.types'
    _description = 'Tipo de turnos: Modelo para creacion de tipo de turnos'
    _rec_name = 'code'

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    opt_turn = fields.Selection([('1','Suma'),('0','Nulo')],string="Accion",default="1")
    default_turn = fields.Boolean(string="Tipo por defecto")

class fortnights(models.Model):
    _name = 'hr.fortnights'
    _description = 'Quincenas: Modelo para crear quincenas'

    name = fields.Char(string="Nombre")
    start_date = fields.Date(string="Fecha inicio")
    end_date = fields.Date(string="Fecha fin")
    line_ids = fields.One2many('hr.fortnights.line','fortnight_id',string="Lineas")
    actual = fields.Boolean(string="Quincenas Actuales")

    def get_fortnights(self):
        fortnights_array = []
        initial_date = self.start_date
        final_date = self.end_date
        while initial_date <= final_date:
            first_day = initial_date.replace(day=1)
            fortnight_day = first_day.replace(day=15)

            if fortnight_day >= initial_date:
                fortnights_array.append((max(initial_date, first_day), min(fortnight_day, final_date)))

            try:
                last_day = first_day.replace(month=first_day.month + 1, day=10) - timedelta(days=1)
            except:
                last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)

            if last_day >= initial_date:
                fortnights_array.append((max(initial_date, fortnight_day + timedelta(days=1)), min(last_day, final_date)))

            initial_date = (first_day + timedelta(days=32)).replace(day=1)
        
        for q in fortnights_array:
            first = q[0]
            last = q[0]
            if first.month < 10:
                number_month = "0%s"%(first.month)
            else:
                number_month = first.month

            if first.day <= 15:
                name_q = "1Q"
            else:
                name_q = "2Q"

            name_line = "%s%s-%s"%(first.year, number_month, name_q)
            vals = {
                'name': name_line,
                'start_date': q[0],
                'end_date': q[1],
                'fortnight_id': self.id
            }

            self.env['hr.fortnights.line'].create(vals)
        return True

class fortnightsLines(models.Model):
    _name = 'hr.fortnights.line'
    _description = 'Lineas de Quincenas: Lineas de quincena'

    name = fields.Char(string="Nombre")
    start_date = fields.Date(string="Fecha inicio")
    end_date = fields.Date(string="Fecha fin")
    fortnight_id = fields.Many2one('hr.fortnights',string="Quincena")
