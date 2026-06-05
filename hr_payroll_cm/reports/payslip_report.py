# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields,_
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class ReportCheckList(models.AbstractModel):
    _name = 'report.hr_payroll_cm.payslip_receipt_cm'
    _description = "Recibo de Nomina CM"

    @api.model
    def _get_report_values(self, docids, data=None):
        # vals = self.get_data(data)
        data = self.get_data(docids)
        docargs = {
            'info_report':data,
        }
        return docargs
	
    def get_data(self,ids):
        payslip_ids = self.env['hr.payslip'].search([('id','in',ids)])
        data = []
        for payslip in payslip_ids:
            incomes_hours = []
            incomes = []
            deductions = []
            salary_worked = 0
            if payslip.worked_days_line_ids:
                line_salary_id = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100')
                if line_salary_id:
                    salary_worked = line_salary_id.amount
                    incomes.append({
                        'name': "Salario",
                        'amount': line_salary_id.amount
                    })

                if salary_worked == 0:
                    salary_worked = payslip.employee_id.wage
                    incomes.insert(0,{
                        'name': 'Salario',
                        'amount': salary_worked
                    })

                for line in payslip.worked_days_line_ids:
                    if line.code != 'WORK100':
                        incomes_hours.append({
                            'name': line.name,
                            'number_of_hours': line.number_of_hours,
                            'amount': line.amount
                        })
            else:
                line_id = payslip.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BASIC')
                if line_id:
                    salary_worked = line_id.total
                else:
                    salary_worked = payslip.employee_id.wage
                incomes.insert(0,{
                    'name': 'Salario',
                    'amount': salary_worked
                })
                        
            for line in payslip.line_ids:
                if line.total != 0:
                    if line.salary_rule_id.category_id.code == 'ALW':
                        incomes.append({
                            'name': line.name,
                            'amount': line.total
                        })

                    if line.salary_rule_id.category_id.code == 'DED':
                        deductions.append({
                            'name': line.name,
                            'amount': abs(line.total)
                        })



            info = {
                'employee_name': payslip.employee_id.name,
                'identification': payslip.employee_id.identification_id,
                'code': payslip.employee_id.barcode,
                'period': payslip.payslip_run_id.name,
                'monthly_wage': payslip.employee_id.monthly_wage,
                'wage': payslip.employee_id.wage,
                'incomes_hours': incomes_hours,
                'incomes': incomes,
                'deductions': deductions,
                'payment_date': self.change_format(payslip.date_to),
            }
            data.append(info)
        return data

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha