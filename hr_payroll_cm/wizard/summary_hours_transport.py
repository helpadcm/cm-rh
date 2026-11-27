from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class summaryHoursTransport(models.TransientModel):
    _name = "hours.transport.summary"
    _description = "Resumen horas y transporte"

    start_date = fields.Date('Fecha Inicial')
    end_date = fields.Date('Fecha Final')

    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        return self.env.ref('hr_payroll_cm.action_inc_ded_payslip_xlsx').report_action(self,data=data)