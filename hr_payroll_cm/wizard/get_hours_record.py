from odoo import models, fields
from babel.dates import format_date

class getRecordHours(models.TransientModel):
    _name = "hr.hours.employees"
    _description = "Hours Record employees"

    date = fields.Date('Date', readonly=True, default=fields.Date.context_today)
    department_id = fields.Many2one('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)

    def get_records(self):
        employees = self.employee_ids
        if not self.employee_ids:
            attendances_ids = self.env['hr.attendance'].search([('check_in', '>=', self.date_from),('check_in', '<=', self.date_to)])
            employees = attendances_ids.mapped('employee_id')

        data_employee = []
        for employee_id in employees:
            if not self.employee_ids:
                id_employee = employee_id.id
            else:
                id_employee = employee_id
            
            employee_report = self.env['hr.attendance.employee.report'].create({
                'employee_id': id_employee,
                'date_from': self.date_from,
                'date_to': self.date_to,
            })

            # Utilizar los métodos del modelo abstracto para obtener y procesar los datos
            employee_attendances = employee_report.get_attendance()
            employee_attendance_data = employee_report.process_employee_attendance()
            emp_data = []
            header_data = employee_attendance_data['header']
            rows_data = employee_attendance_data['rows']

            contract_id = self.env['hr.contract'].search([('employee_id','=',id_employee)])
            rec_id = self.env['hr.employee.attendance.record'].create({
                'name': 'Registro de Asistencia %s %s'%(header_data.get('employee'), header_data.get('start_date')),
                'period': 'Periodo %s - %s'%(header_data.get('start_date').strftime("%d/%m/%Y"), header_data.get('end_date').strftime("%d/%m/%Y")),
                'employee_id': header_data.get('employee_id'),
                'code': header_data.get('employee_no'),
                'start_date': header_data.get('start_date'),
                'end_date': header_data.get('end_date'),
                'esperated_hours': header_data.get('expected_hours'),
                'eh_limit': contract_id.max_extra_hours,
                'tb_max': contract_id.max_transportation_bonus,
                'tb_bonus': contract_id.value_bonus,
                'tb_limit': contract_id.max_transportation_bonus * contract_id.value_bonus
            })

            for row in rows_data:
                self.env['hr.employee.attendance.line'].create({
                    'attendance_rec_id': rec_id.id,
                    'date': row.get('date'),
                    'day': format_date(row.get("date"), "EEEE", locale="es"),
                    'check_in_1': row.get('check_in_1').strftime("%H:%M:%S") if row.get("check_in_1") else "",
                    'check_out_1': row.get('check_out_1').strftime("%H:%M:%S") if row.get("check_out_1") else "",
                    'check_in_2': row.get('check_in_2').strftime("%H:%M:%S") if row.get("check_in_2") else "",
                    'check_out_2': row.get('check_out_2').strftime("%H:%M:%S") if row.get("check_out_2") else "",
                    'check_in_3': row.get('check_in_3').strftime("%H:%M:%S") if row.get("check_in_3") else "",
                    'check_out_3': row.get('check_out_3').strftime("%H:%M:%S") if row.get("check_out_3") else "",
                    'total_hours': row.get('total_hours'),
                    'ordinary_hours': row.get('ordinary_hours'),
                    'extra_hours': row.get('extra_hours'),
                    'observations': row.get('observation'),
                    'bonus': row.get('transport_bonus'),
                })
        return True