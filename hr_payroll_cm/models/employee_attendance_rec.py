from odoo import fields, models, api


class employeeAttendanceRecords(models.Model):
    _name = 'hr.employee.attendance.record'
    _description = 'Registro de asistencia de empleados'

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
    total_hours = fields.Float(string="Horas Totales",compute='compute_eh_totals',help="Suma de horas trabajadas + total horas extras")
    diff_hours = fields.Float(string="Dif. Horas",compute='compute_eh_totals',help="Diferencia Total de horas - Horas esperadas")
    eh_pay = fields.Float(string="Pagar HE",compute='compute_eh_totals',help="Horas Extras a pagar ")
    aditional_he = fields.Float(string="HE adicionales",compute='compute_eh_totals',help="Horas extras restantes")
    tb_bonus = fields.Float(string="Valor de Bono")
    tb_limit = fields.Float(string="BT Limite",help="BT Maximo * Valor Bono")


    @api.depends('record_line_ids')
    def compute_eh_totals(self):
        for rec in self:
            if rec.record_line_ids:
                hours_total = 0
                eh_total = 0
                for line in rec.record_line_ids:
                    hours_total += line.ordinary_hours
                    eh_total += line.extra_hours
                rec.total_hours = hours_total + eh_total
                rec.diff_hours = rec.total_hours - rec.esperated_hours
                if rec.diff_hours <= rec.eh_limit:
                    rec.eh_pay = rec.diff_hours
                    rec.aditional_he = 0
                elif rec.diff_hours > rec.eh_limit:
                    rec.eh_pay = rec.eh_limit
                    rec.aditional_he = rec.diff_hours - rec.eh_limit

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
    ordinary_hours = fields.Integer(string="HO")
    extra_hours = fields.Float(string="HE")
    observations = fields.Char(string="Observaciones")
    bonus = fields.Float(string="BT")
    attendance_rec_id = fields.Many2one('hr.employee.attendance.record',string="Registro de asistencia")

