from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from calendar import monthrange

class workTeams(models.Model):
    _name = 'hr.work.teams'
    _description = 'Teams: Work teams'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Name',tracking=True)
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo",tracking=True)
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo",tracking=True)
    active = fields.Boolean(string="Activo", default=True,tracking=True)
    send_email = fields.Boolean(string="Enviar notificacion")
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
    color = fields.Char(string="Color")
    active = fields.Boolean(string="Activo",default=True)

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

        final_date = self.end_date
        init_date = self.start_date

        initial_date = self.start_date.replace(day=1)
        
        while initial_date <= final_date:
            _, month_days = monthrange(initial_date.year, initial_date.month)


            initial_first_fortnight = initial_date.replace(day=1)
            final_first_fortnight = initial_date.replace(day=15)

            initial_second_fortnight = initial_date.replace(day=16)
            final_second_fortnight = initial_date.replace(day=month_days)
            
            if initial_first_fortnight <= final_date and final_first_fortnight >= init_date:
                fortnights_array.append((max(init_date, initial_first_fortnight), min(final_date, final_first_fortnight)))

            if initial_second_fortnight <= final_date and final_second_fortnight >= init_date:
                fortnights_array.append((max(init_date, initial_second_fortnight), min(final_date, final_second_fortnight)))

            initial_date = (initial_date + timedelta(days=month_days)).replace(day=1)
        
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

class notificationEmails(models.Model):
    _name = 'turn.email.notifications'
    _description = 'Listado de correos notificacion de turnos'

    name = fields.Char(string="Nombre")
    line_ids = fields.One2many('email.notifications.line','notification_id',string="Lineas")

class emailLines(models.Model):
    _name = 'email.notifications.line'
    _description = 'Lineas de correos para notificacion'

    employee_id = fields.Many2one('hr.employee',string="Empleado")
    email = fields.Char(string="Correo")
    notification_id = fields.Many2one('turn.email.notifications',string="Notificacion")

    @api.onchange('employee_id')
    def get_email(self):
        if self.employee_id:
            self.email = self.employee_id.work_email
