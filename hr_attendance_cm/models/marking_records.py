from odoo import fields, models, api
from datetime import datetime, timedelta, time


class markingRealEmployees(models.Model):
    _name = 'real.marking.employees'
    _description = 'Marcajes reales de empleados'

    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one('hr.employee',string='Empleado')
    date =  fields.Date(string="Fecha")
    employee_code = fields.Char(string="Codigo de empleado")
    state = fields.Selection([('draft','Borrador'),('finalized','Finalizado')],string="Estado",default="draft")
    marking_ids = fields.One2many('list.marking.employees','marking_id',string="Listado de Marcajes")
    lost_marking = fields.Boolean(string="Marcajes perdidos")
    qty_marks = fields.Integer(string="Cant. Lineas",compute="_calculate_lines_qty")

    @api.depends('marking_ids')
    def _calculate_lines_qty(self):
        for rec in self:
            rec.qty_marks = len(rec.marking_ids)

    def create_attendance(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            marking_record_ids = self.search([('state','=','draft')])
        else:
            marking_record_ids = self.search([('state','=','draft'),('id','in',active_ids)])

        marking_data = []
        attendance_obj = self.env['hr.attendance']
        for mark in marking_record_ids:
            if mark.lost_marking:
                self.delete_attendances(mark)
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
                            'attendance_date': mark.date,
                            'check_in': line.date
                        }
                    count += 1
                mark.state = 'finalized'
            elif lines_qty == 3:
                min_date = mark.marking_ids[0].date
                max_date = mark.marking_ids[0].date
                clock_in_id = mark.marking_ids[0].clock_id
                clock_out_id = mark.marking_ids[0].clock_id

                for line in mark.marking_ids:
                    if line.date < min_date:
                        min_date = line.date
                        clock_in_id = line.clock_id
                    elif line.date > max_date:
                        max_date = line.date
                        clock_out_id = line.clock_id

                vals = {
                    'employee_id': mark.employee_id.id,
                    'in_device_id': clock_in_id.id,
                    'check_in': min_date,
                    'attendance_date': mark.date,
                    'out_device_id': clock_out_id.id,
                    'check_out': max_date,
                    'in_mode': 'attendance_system'
                }
                attendance_obj.create(vals)
                mark.state = 'finalized'
            elif lines_qty == 5:
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
                        if count != 5:
                            vals = {
                                'employee_id': mark.employee_id.id,
                                'in_device_id': line.clock_id.id,
                                'in_mode': 'attendance_system',
                                'attendance_date': mark.date,
                                'check_in': line.date
                            }
                        else:
                            vals = {
                                'employee_id': mark.employee_id.id,
                                'in_device_id': line.clock_id.id,
                                'check_in': line.date,
                                'out_device_id': line.clock_id.id,
                                'check_out': line.date,
                                'attendance_date': mark.date,
                                'in_mode': 'attendance_system',
                                'observations': 'En uno de los turnos se realizo una sola marca'
                            }
                            attendance_obj.create(vals)

                    count += 1
                mark.state = 'finalized'
            elif lines_qty == 1:
                vals = {
                    'employee_id': mark.employee_id.id,
                    'in_device_id': mark.marking_ids[0].clock_id.id,
                    'check_in': mark.marking_ids[0].date,
                    'out_device_id': mark.marking_ids[0].clock_id.id,
                    'check_out': mark.marking_ids[0].date,
                    'attendance_date': mark.date,
                    'in_mode': 'attendance_system',
                    'observations': 'En uno de los turnos se realizo una sola marca'
                }
                attendance_obj.create(vals)
                mark.state = 'finalized'

    def delete_attendances(self,mark):
        attendance_ids = self.env['hr.attendance'].search([('attendance_date','=',mark.date),('employee_id','=',mark.employee_id.id)])
        if attendance_ids:
            attendance_ids.unlink()
        mark.lost_marking = False

    def show_absences(self):
        consult_initial_date = datetime.combine(self.date, datetime.min.time())
        consult_final_date = datetime.combine(self.date, time(23,59))
        attendance_ids = self.env['hr.attendance'].search([('attendance_date','=',consult_initial_date),('employee_id','=',self.employee_id.id)])
        if attendance_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Listado de Asistencias',
                'view_mode': 'list',
                'res_model': 'hr.attendance',
                'views': [(self.env.ref('hr_attendance.view_attendance_tree').id, 'list')],
                'domain': [('id','=',attendance_ids.ids)],
                'target': 'current',
                'context': self.env.context
            }
        else:
            return True

class listMarkingEmployees(models.Model):
    _name = 'list.marking.employees'
    _description = 'Lista de Marcajes reales de empleados'
    _order = 'date asc'

    date =  fields.Datetime(string="Fecha y Hora Marcaje")
    clock_id = fields.Many2one('hr.attendance.device',string="Reloj Marcador")
    marking_id = fields.Many2one('real.marking.employees',string="Marcaje")
