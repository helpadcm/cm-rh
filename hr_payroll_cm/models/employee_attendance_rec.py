from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

actions = [
    ('free', 'Libre'),
    ('inc', 'Incapacidad'),
    ('special', 'Permiso Especial'),
    ('vac', 'Vacaciones'),
    ('wh', 'Feriado Trabajado'),
    ('cap', 'Capacitacion'),
    ('coe', 'Cubrir en otra estación'),
    ('na', 'Sin Registro'),
    ('holiday', 'Feriado'),
    ('comp', 'Compensatorio'),
    ('homeoffice', 'Home Office'),
    ('other', 'Otros'),
]

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class employeeAttendanceRecords(models.Model):
    _name = 'hr.employee.attendance.record'
    _description = 'Registro de asistencia de empleados'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "payslip_date_from desc, employee_id asc"

    name = fields.Char('Name')
    period = fields.Char(string="Periodo")
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    code = fields.Char(string="Código de empleado")
    start_date = fields.Date(string="Fecha de inicio")
    end_date = fields.Date(string="Fecha fin")
    esperated_hours = fields.Integer(string="Horas esperadas")
    record_line_ids = fields.One2many('hr.employee.attendance.line','attendance_rec_id',string="Lineas de asistencia")
    eh_limit = fields.Float(string="HE Limite")
    tb_max = fields.Integer(string="BT Maximo")
    total_hours = fields.Float(string="Horas Totales",compute='compute_eh_totals',help="Suma de horas trabajadas + total horas extras", store=True)
    diff_hours = fields.Float(string="Dif. Horas",compute='compute_eh_totals',help="Diferencia Total de horas - Horas esperadas", store=True)
    eh_pay = fields.Float(string="Pagar HE",compute='compute_eh_totals',help="Horas Extras a pagar ", store=True)
    real_eh_pay = fields.Float(string="Total HE",help="Horas Extras reales a pagar",tracking=True)
    pay_extra_hours = fields.Float(string="HE Real",help="Horas Extras reales",compute="get_eh_real")
    aditional_he = fields.Float(string="Compensatorio",compute='compute_eh_totals',help="Horas extras restantes", store=True)
    real_aditional_he = fields.Float(string="Compensatorias Reales", help="Horas compensatorias reales a aplicar",tracking=True)
    tb_bonus = fields.Float(string="Valor de Bono")
    tb_limit = fields.Float(string="BT Limite",help="BT Maximo * Valor Bono")
    tb_pay = fields.Float(string="Pagar BT",help="BT a pagar",compute='compute_eh_totals', store=True)
    eh_holiday = fields.Float(string="Horas Feriado",compute='compute_eh_totals', store=True)
    eh_holiday_extra = fields.Float(string="HE Feriado",compute='compute_eh_totals', store=True)
    state = fields.Selection([('draft','Borrador'),('revised','Revisado'),('finalized','Finalizado')],string="Estado",default='draft',tracking=True)
    payslip_date_from = fields.Date('Fecha Inicio Nomina')
    payslip_date_to = fields.Date('Fecha Fin Nomina')
    department_id = fields.Many2one('hr.department',string="Departamento")
    sum_compensatory = fields.Boolean(string="Sumar Compensatorio",default=True,tracking=True)

    hours_25 = fields.Float(string="HE 25%",help="Horas extras al 25%", tracking=True)
    hours_50 = fields.Float(string="HE 50%",help="Horas extras al 50%", tracking=True)
    hours_75 = fields.Float(string="HE 75%",help="Horas extras al 75%", tracking=True)

    def update_real_eh(self):
        if self.diff_hours > 0:
            if self.diff_hours > self.eh_limit:
                self.real_eh_pay = self.eh_limit
            else:
                self.real_eh_pay = self.diff_hours
        else:
            self.real_eh_pay = 0

    @api.onchange('hours_25','hours_50','hours_75')
    def update_hr_real(self):
        for rec in self:
            rec.real_eh_pay = rec.hours_25 + rec.hours_50 + rec.hours_75

    def update_name(self):
        name = ''
        if self.payslip_date_from.day == 1:
            name = 'Primera Quincena %s %s'%(months[self.payslip_date_from.month - 1], self.payslip_date_from.year)
        elif self.payslip_date_from.day == 16:
            name = 'Segunda Quincena %s %s'%(months[self.payslip_date_from.month - 1], self.payslip_date_from.year)
        self.period = name

    @api.onchange('aditional_he')
    def get_aditional_he(self):
        self.real_aditional_he = self.aditional_he

    @api.depends('eh_pay','real_eh_pay')
    def get_eh_real(self):
        for rec in self:
            if rec.eh_pay > 0 and rec.real_eh_pay == 0:
                rec.pay_extra_hours = rec.eh_pay
            elif rec.real_eh_pay > 0:
                rec.pay_extra_hours = rec.real_eh_pay
            else:
                rec.pay_extra_hours = 0

    def get_department(self):
        self.department_id = self.employee_id.department_id.id

    def change_state(self):
        next_state = self.env.context.get('next_stage')
        aditional_he_real = 0
        if self.real_aditional_he != 0:
            aditional_he_real = self.real_aditional_he
        else:
            aditional_he_real = self.aditional_he
        
        if next_state == 'finalized':
            if self.sum_compensatory:
                self.employee_id.compensatory_hours += aditional_he_real

        if next_state == 'draft':
            if self.sum_compensatory:
                self.employee_id.compensatory_hours -= aditional_he_real
        self.state = next_state

    def add_aditional_hours(self):
        if self.state == 'finalized' and self.sum_compensatory:
            self.employee_id.compensatory_hours += self.aditional_he


    @api.depends('record_line_ids')
    def compute_eh_totals(self):
        for rec in self:
            if rec.record_line_ids:
                hours_total = 0
                eh_total = 0
                holiday_hours = 0
                e_holiday_hours = 0
                pay_bt = 0
                for line in rec.record_line_ids:
                    hours_total += line.ordinary_hours
                    eh_total += line.extra_hours
                    pay_bt += line.bonus
                    if line.personal_action == 'wh':
                        holiday_hours += line.holiday_hours
                        e_holiday_hours += line.holiday_extra_hours

                    if line.personal_action == 'cap':
                        eh_total -= line.extra_hours

                    if line.personal_action == 'vac' and line.special_hours > 0:
                        hours_total -= line.ordinary_hours
                        hours_total += line.special_hours

                    if line.special_hours > 0 and line.personal_action != 'vac':
                        hours_total += line.special_hours

                if pay_bt > rec.tb_limit:
                    pay_bt = rec.tb_limit

                rec.tb_pay = pay_bt
                rec.eh_holiday = holiday_hours
                rec.eh_holiday_extra = e_holiday_hours
                rec.total_hours = hours_total + eh_total
                rec.diff_hours = rec.total_hours - rec.esperated_hours
                if rec.diff_hours <= rec.eh_limit:
                    if rec.diff_hours > 0:
                        rec.eh_pay = rec.diff_hours
                    else:
                        rec.eh_pay = 0
                    rec.aditional_he = 0
                elif rec.diff_hours > rec.eh_limit:
                    rec.eh_pay = rec.eh_limit
                    rec.aditional_he = rec.diff_hours - rec.eh_limit

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('No se pueden eliminar registros revisados o finalizados')
        res = super(employeeAttendanceRecords, self).unlink()
        return res
                
    

class lineAttendanceRecords(models.Model):
    _name = 'hr.employee.attendance.line'
    _description = 'Lineas de registro de asistencia de empleados'

    date = fields.Date(string="Fecha")
    day = fields.Char(string="Dia")
    check_in_1 = fields.Char(string="Turno 1(Entrada)")
    check_out_1 = fields.Char(string="Turno 1(Salida)")
    check_in_2 = fields.Char(string="Turno 2(Entrada)")
    check_out_2 = fields.Char(string="Turno 2(Salida)")
    check_in_3 = fields.Char(string="Turno 3(Entrada)")
    check_out_3 = fields.Char(string="Turno 3(Salida)")
    total_hours = fields.Float(string="Trabajadas")
    ordinary_hours = fields.Float(string="HO")
    extra_hours = fields.Float(string="HE")
    holiday_hours = fields.Float(string="FO")
    holiday_extra_hours = fields.Float(string="FE")
    observations = fields.Char(string="Observaciones")
    bonus = fields.Float(string="BT")
    attendance_rec_id = fields.Many2one('hr.employee.attendance.record',string="Registro de asistencia")
    personal_action = fields.Selection(actions, string="Acciones de personal")
    special_hours = fields.Float(string="Horas Especiales")
    notes =fields.Char(string="Nota")

    schedule1_in_date = fields.Char(string="Entrada 1")
    schedule1_out_date = fields.Char(string="Salida 1")
    turn_type_a = fields.Many2one('hr.turn.types',string="Tipo Turno A")
    schedule2_in_date = fields.Char(string="Entrada 2")
    schedule2_out_date = fields.Char(string="Salida 2")
    turn_type_b = fields.Many2one('hr.turn.types',string="Tipo Turno B")
    turn_note = fields.Text(string="Notas de turno")
    check_type = fields.Selection([('mark','Marcaje'),('turn','Planificación')],string="Revisar segun")

    @api.onchange('personal_action')
    def personal_action_change(self):
        if self.personal_action:
            self.observations = dict(self._fields['personal_action'].selection).get(self.personal_action, '')
            if self.personal_action == 'free':
                self.ordinary_hours = 0
            elif self.personal_action in ['holiday','inc','special','comp','vac','cap']:
                self.ordinary_hours = 8

    @api.onchange('check_type')
    def calculate_data(self):
        for rec in self:
            amount1 = 0
            amount2 = 0
            amount3 = 0
            bonus = 0
            min_hours = []
            max_hours = []

            if rec.check_type == 'turn':

                amount1, hour_1, hour_2 = self._calculate_hours(
                    rec.schedule1_in_date,
                    rec.schedule1_out_date
                )

                if hour_1 is not None:
                    min_hours.append(hour_1)
                    max_hours.append(hour_2)

                amount2, hour_1, hour_2 = self._calculate_hours(
                    rec.schedule2_in_date,
                    rec.schedule2_out_date
                )

                if hour_1 is not None:
                    min_hours.append(hour_1)
                    max_hours.append(hour_2)

            else:

                amount1, hour_1, hour_2 = self._calculate_hours(
                    rec.check_in_1,
                    rec.check_out_1
                )

                if hour_1 is not None:
                    min_hours.append(hour_1)
                    max_hours.append(hour_2)

                amount2, hour_1, hour_2 = self._calculate_hours(
                    rec.check_in_2,
                    rec.check_out_2
                )

                if hour_1 is not None:
                    min_hours.append(hour_1)
                    max_hours.append(hour_2)

                amount3, hour_1, hour_2 = self._calculate_hours(
                    rec.check_in_3,
                    rec.check_out_3
                )

                if hour_1 is not None:
                    min_hours.append(hour_1)
                    max_hours.append(hour_2)

            bonus = self.calculate_bonus(min_hours, max_hours)

            rec.bonus = bonus
            rec.total_hours = amount1 + amount2 + amount3

            if rec.total_hours > 0:
                rec.ordinary_hours = min(rec.total_hours, 8)
                rec.extra_hours = max(rec.total_hours - 8, 0)
            else:
                rec.ordinary_hours = 0
                rec.extra_hours = 0

    def _calculate_hours(self, start, end):
        try:
            hour_1 = self.convert_timedelta(start)
            hour_2 = self.convert_timedelta(end)

            diff = hour_2 - hour_1

            # Si la salida es después de medianoche,
            # significa que pertenece al día siguiente.
            if diff.total_seconds() < 0:
                diff += timedelta(days=1)

            return (
                diff.total_seconds() / 3600,
                hour_1.total_seconds() / 3600,
                hour_2.total_seconds() / 3600,
            )

        except Exception:
            return 0, None, None

    def convert_timedelta(self, hour):
        h, m, s = map(int, hour.split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)

    def calculate_bonus(self, check1, check2):
        employee_id = self.attendance_rec_id.employee_id
        bonus = 0
        if check1:
            if min(check1) < employee_id.early_checkin_bonus_time:
                bonus += employee_id.value_bonus
        if check2:
            if max(check2) > employee_id.late_checkout_bonus_time:
                bonus += employee_id.value_bonus
        return bonus