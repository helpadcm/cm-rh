from odoo import fields, models
from datetime import datetime, timedelta


class markingRealEmployees(models.Model):
    _name = 'real.marking.employees'
    _description = 'Marcajes reales de empleados'

    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one('hr.employee',string='Empleado')
    date =  fields.Date(string="Fecha")
    employee_code = fields.Char(string="Codigo de empleado")
    state = fields.Selection([('draft','Borrador'),('finalized','Finalizado')],string="Estado",default="draft")
    marking_ids = fields.One2many('list.marking.employees','marking_id',string="Listado de Marcajes")

    def create_attendance(self):
        marking_record_ids = self.search([('state','=','draft')])
        marking_data = []
        attendance_obj = self.env['hr.attendance']
        for mark in marking_record_ids:
            lines_qty = len(mark.marking_ids)
            if lines_qty in [2,4,6]:
                count = 1
                for line in mark.marking_ids:
                    if count % 2 == 0:
                        vals.update({
                            'out_device_id': line.clock_id.id
                        })
                        if vals.get('check_in') > line.date:
                            vals.update({'check_in': line.date, 'check_out': vals.get('check_in')})
                        else:
                            vals.update({'check_out': line.date})


                        attendance_obj.create(vals)
                    else:
                        vals = {
                            'employee_id': mark.employee_id.id,
                            'in_device_id': line.clock_id.id,
                            'in_mode': 'attendance_system',
                            'check_in': line.date
                        }
                    count += 1
                mark.state = 'finalized'
            elif lines_qty == 3:
                vals = {
                    'employee_id': mark.employee_id.id,
                    'in_device_id': mark.marking_ids[0].clock_id.id,
                    'check_in': mark.marking_ids[0].date,
                    'out_device_id': mark.marking_ids[2].clock_id.id,
                    'check_out': mark.marking_ids[2].date,
                    'in_mode': 'attendance_system'
                }
                attendance_obj.create(vals)
                mark.state = 'finalized'
            elif lines_qty == 1:
                vals = {
                    'employee_id': mark.employee_id.id,
                    'in_device_id': mark.marking_ids[0].clock_id.id,
                    'check_in': mark.marking_ids[0].date,
                    'in_mode': 'attendance_system'
                }
                attendance_obj.create(vals)
                mark.state = 'finalized'

class listMarkingEmployees(models.Model):
    _name = 'list.marking.employees'
    _description = 'Lista de Marcajes reales de empleados'

    date =  fields.Datetime(string="Fecha y Hora Marcaje")
    clock_id = fields.Many2one('hr.attendance.device',string="Reloj Marcador")
    marking_id = fields.Many2one('real.marking.employees',string="Marcaje")
