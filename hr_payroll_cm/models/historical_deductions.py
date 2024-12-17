from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class historicalDeductions(models.Model):
    _name = 'hr.historical.deductions'
    _description = 'Historicos: Listado de Deducciones '

    name = fields.Char(string="Nombre")
    amount = fields.Float(string="Monto")
    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha de Fin")
    payslip_id = fields.Many2one('hr.payslip',string="Nomina")
    code = fields.Char(string="Codigo")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
