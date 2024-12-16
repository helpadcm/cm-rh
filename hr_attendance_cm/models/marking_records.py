from odoo import fields, models


class markingRealEmployees(models.Model):
    _name = 'real.marking.employees'
    _description = 'Marcajes reales de empleados'

    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one('hr.employee',string='Empleado')
    date =  fields.Date(string="Fecha")
    employee_code = fields.Char(string="Codigo de empleado")
    marking_ids = fields.One2many('list.marking.employees','marking_id',string="Listado de Marcajes")

class listMarkingEmployees(models.Model):
    _name = 'list.marking.employees'
    _description = 'Lista de Marcajes reales de empleados'

    date =  fields.Datetime(string="Fecha y Hora Marcaje")
    clock_id = fields.Many2one('hr.attendance.device',string="Reloj Marcador")
    marking_id = fields.Many2one('real.marking.employees',string="Marcaje")
