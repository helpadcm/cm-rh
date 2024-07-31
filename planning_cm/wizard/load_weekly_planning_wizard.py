import base64
import io
from datetime import datetime, timedelta, time

import xlrd
from pytz import timezone

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoadPlanningWizard(models.TransientModel):
    _name = 'load.planning.wizard'
    _description = 'Load Weekly Planning Wizard'

    def _get_default_week_number(self):
        return datetime.now().isocalendar()[1]

    def _get_first_date_of_week(self):
        current_year = datetime.now().year
        first_day_of_year = datetime(current_year, 1, 1)
        first_week_number, first_week_day = first_day_of_year.isocalendar()[1:3]
        week_diff = self.week_number - first_week_number
        if first_week_day == 1:
            start_date = first_day_of_year + timedelta(weeks=week_diff)
        else:
            days_to_first_monday = 7 - first_week_day + 1
            start_date = first_day_of_year + timedelta(days=days_to_first_monday, weeks=week_diff)
        return start_date

    @api.depends('week_number')
    def _compute_default_start_date(self):
        self.start_date = self._get_first_date_of_week()

    @api.depends('week_number')
    def _compute_default_end_date(self):
        self.end_date = self._get_first_date_of_week() + timedelta(days=6)

    week_number = fields.Integer(string='Week Number', default=_get_default_week_number)
    start_date = fields.Date(string='Start Date', readonly=True, compute='_compute_default_start_date')
    end_date = fields.Date(string='End Date', readonly=True, compute='_compute_default_end_date')
    data_file = fields.Binary(string='Data File', attachment=False)
    start_row = fields.Integer(string='Start Row', default=9)
    number_of_employee = fields.Integer(string='Number of Employee', default=0)

    valid_rows = fields.Integer(string='Valid Rows', readonly=True)

    employee_ids = fields.Many2many('hr.employee', string='Employees', readonly=True)
    resource_ids = fields.Many2many('resource.resource', string='Resources', compute='_compute_resource_ids')

    @api.onchange('week_number')
    def _onchange_week_number(self):
        if self.week_number:
            self._compute_default_start_date()
            self._compute_default_end_date()

    @api.depends('employee_ids')
    def _compute_resource_ids(self):
        self.resource_ids = self.employee_ids.mapped('resource_id')

    def _get_sheet_from_file(self):
        file_data = base64.b64decode(self.data_file)
        file_stream = io.BytesIO(file_data)
        workbook = xlrd.open_workbook(file_contents=file_stream.read())
        return workbook.sheet_by_index(0)

    def _get_planning_from_rows(self, sheet):
        planning = []
        for row in range(self.start_row, self.number_of_employee + self.start_row):
            employee_id = sheet.cell_value(row, 1)
            employee_name = sheet.cell_value(row, 2)
            if not employee_id or not employee_name:
                continue
            employee_planning = {
                'employee_id': employee_id,
                'employee_name': employee_name,
                'days': []
                }
            for col in range(3, 30, 2):
                start_time = sheet.cell_value(row, col)
                end_time = sheet.cell_value(row, col + 1)
                if start_time and end_time:
                    employee_planning['days'].append(
                        {
                            'start_time': start_time,
                            'end_time': end_time
                            }
                        )
                else:
                    employee_planning['days'].append(None)
            planning.append(employee_planning)
        return planning

    def _clean_weekly_planning_slots(self):
        self.env['planning.slot'].search(
            [
                ('resource_id', 'in', self.resource_ids.ids),
                ('start_datetime', '>=', self.start_date),
                ('end_datetime', '<=', self.end_date)
                ]
            ).unlink()

    def float_to_time(self, float_time):
        total_seconds = float_time * 86400  # Convert float time to total seconds in the day
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return time(hour=hours, minute=minutes, second=seconds)

    def action_show_notification(self, title, message, type='info'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
                'type': type,
                },
            }

    def action_test(self):
        if not self.data_file:
            raise ValidationError(_("Please upload a file to test."))
        # Decodificar el archivo binario
        sheet = self._get_sheet_from_file()
        planning = self._get_planning_from_rows(sheet)
        self.employee_ids = self.env['hr.employee'].search([('barcode', 'in', [p['employee_id'] for p in planning])])

        self.valid_rows = len(planning)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Test Results'),
            'view_mode': 'form',
            'res_model': 'load.planning.wizard',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context
            }

    def action_load_planning(self):
        if not self.data_file:
            raise ValidationError(_("Please upload a file to load planning."))
        sheet = self._get_sheet_from_file()
        planning = self._get_planning_from_rows(sheet)
        self.employee_ids = self.env['hr.employee'].search([('barcode', 'in', [p['employee_id'] for p in planning])])
        self._clean_weekly_planning_slots()
        for employee in self.employee_ids:
            employee_planning = [p for p in planning if p['employee_id'] == employee.barcode][0]
            resource_id = self.env['resource.resource'].search([('employee_id', '=', employee.id)], limit=1)
            planning_slots = []
            for day, day_planning in zip((day for day in range(0, 7) for _ in range(2)), employee_planning['days']):
                if day_planning:
                    planning_slot = {
                        'resource_id': resource_id.id,
                        'start_datetime': datetime.combine(
                            self.start_date + timedelta(days=day), self.float_to_time(day_planning['start_time'])
                            ).astimezone(timezone(self.env.user.tz)),
                        'end_datetime': datetime.combine(
                            self.start_date + timedelta(days=day), self.float_to_time(day_planning['end_time'])
                            ).astimezone(timezone(self.env.user.tz))
                        }
                    planning_slots.append(planning_slot)
                    self.env['planning.slot'].create(planning_slots)
                    self.action_show_notification(
                        title=_('Success'),
                        message=f"Planificación exitosa para {employee.name}.",
                        type='success'
                        )
                    self.action_show_notification(
                        title=_('Success'),
                        message=f"Planificación exitosa para {self.number_of_employee} empleados.",
                        type='success'
                        )
        return {'type': 'ir.actions.act_window_close'}
