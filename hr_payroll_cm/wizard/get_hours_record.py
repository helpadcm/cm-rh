from odoo import models, fields, _, api
from babel.dates import format_date
import calendar

class getRecordHours(models.TransientModel):
    _name = "hr.hours.employees"
    _description = "Hours Record employees"

    date = fields.Date('Date', readonly=True, default=fields.Date.context_today)
    department_id = fields.Many2one('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)

    payslip_date_from = fields.Date(_('Start Date Pasylip'))
    payslip_date_to = fields.Date(_('End Date Payslip'))

    @api.onchange('date_from')
    def get_payslips_date(self):
        if self.date_from:
            year = self.date_from.year
            month = self.date_from.month
            if self.date_from.day >= 26:
                if month == 12:
                    date_from_payslip = "%s-%s-%s"%(year + 1, '01', '01')
                    date_to_payslip = "%s-%s-%s"%(year + 1, '01', 15)
                else:
                    date_from_payslip = "%s-%s-%s"%(year, month + 1, '01')
                    date_to_payslip = "%s-%s-%s"%(year, month + 1, 15)
            elif self.date_from.day <= 26:
                _, num_days = calendar.monthrange(year, month)
                date_from_payslip = "%s-%s-%s"%(year, month, 16)
                date_to_payslip = "%s-%s-%s"%(year, month, num_days)
            self.payslip_date_from = date_from_payslip
            self.payslip_date_to = date_to_payslip

    def get_records(self):
        employees = self.employee_ids
        if not self.employee_ids:
            attendances_ids = self.env['hr.attendance'].search([('check_in', '>=', self.date_from),('check_in', '<=', self.date_to)])
            employees = attendances_ids.mapped('employee_id')
        else:
            employees = self.employee_ids.ids

        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id','=',self.department_id.id)])

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
                'department_id': contract_id.employee_id.department_id.id,
                'code': header_data.get('employee_no'),
                'start_date': header_data.get('start_date'),
                'end_date': header_data.get('end_date'),
                'esperated_hours': header_data.get('expected_hours'),
                'eh_limit': contract_id.max_extra_hours,
                'tb_max': contract_id.max_transportation_bonus,
                'tb_bonus': contract_id.value_bonus,
                'tb_limit': contract_id.max_transportation_bonus * contract_id.value_bonus,
                'payslip_date_from': self.payslip_date_from,
                'payslip_date_to': self.payslip_date_to
            })

            for row in rows_data:
                vals = {
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
                }
                turn_line_id = self.env['hr.turn.registration'].search([('employee_id','=',id_employee),('date','=',row.get('date'))])
                if turn_line_id:
                    print ("////////////////////////")
                    entry_date_1 = self.convert_format(turn_line_id.schedule1_in_id)
                self.env['hr.employee.attendance.line'].create(vals)
        return True

    def convert_format(self, schedule_id):
        if not schedule_id.alphabetical:
            print (schedule_id.name)
            print (a)
        return True