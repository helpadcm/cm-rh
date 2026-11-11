from odoo import models, fields
from odoo.tools import float_round  # <--- IMPORTANTE
import base64
import io
from collections import OrderedDict

class lotFormatXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_cm.lot_format_cm_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Formato de nomina XLS"

    def generate_xlsx_report(self, workbook, data, docids):
        info = self.get_data(docids.ids)
        sheet = workbook.add_worksheet('Planilla')

        # Obtener precisión de la moneda
        company = self.env.user.company_id
        precision = company.currency_id.decimal_places or 2

        if company.logo:
            image_data = io.BytesIO(base64.b64decode(company.logo))
            sheet.insert_image('A1', 'logo.png', {'image_data': image_data, 'x_scale': 0.2, 'y_scale': 0.15})

        # Formatos
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        header_format = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'color': '#000000', 'border': 2, 'text_wrap':True})
        dept_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'right': True, 'left': True})
        dept_name_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'border': 1})
        money_format = workbook.add_format({'font_size': 10, 'num_format': '#,##0.00','text_wrap':True,'right': True, 'left': True})
        totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})
        count_format = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True, 'right': True, 'left': True, 'color': '#FF0000'})
        total_totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})

        count_format.set_align('center')
        header_format.set_align('center')
        header_format.set_align('vcenter')
        format1.set_align('center')

        company_name = company.name
        sheet.merge_range('D2:M2', company_name, format1)
        sheet.merge_range('D3:M3', info.get('payslip_name'), format1)

        # Columnas base
        headers = [
            'No.', 'Fecha de ingreso', 'ID', 'No. de cuenta', 'Empleado', 'Puesto'
        ]

        # Agregar reglas salariales dinámicamente
        headers += info.get('incomes_name', []) + ['Total Devengado']
        headers += info.get('deductions_name', []) + ['Total Deducciones', 'TOTAL NETO A PAGAR']

        # Escribir encabezados
        for col, header in enumerate(headers):
            sheet.write(6, col, header, header_format)
            if col == 0:
                sheet.set_column(col, col, 5)
            else:
                sheet.set_column(col, col, 15)

        row = 7
        emp_count = 1
        grand_totals = {name: 0.0 for name in headers[6:]}

        # Iterar sobre departamentos y empleados agrupados
        for department_name, department_info in info.get('department_data').items():
            dept_totals = {name: 0.0 for name in headers[6:]}

            for employee in department_info.get('employees'):
                # Redondear montos individuales antes de sumar
                total_ingresos = float_round(
                    sum(float_round(x['amount'], precision_digits=precision) 
                        for x in employee.get('incomes') if x.get('code') not in ['EXT25','EXT50','EXT75','SM','HEFF','HFF']),
                    precision_digits=precision
                )
                total_devengado = total_ingresos

                total_deducciones = float_round(
                    abs(sum(float_round(x['amount'], precision_digits=precision) 
                            for x in employee.get('deductions'))),
                    precision_digits=precision
                )

                total_neto = employee.get('net_amount', 0.0)

                # Acumular valores al total del departamento usando float_round
                dept_totals['Total Devengado'] = float_round(dept_totals['Total Devengado'] + total_devengado, precision_digits=precision)
                dept_totals['Total Deducciones'] = float_round(dept_totals['Total Deducciones'] + total_deducciones, precision_digits=precision)
                dept_totals['TOTAL NETO A PAGAR'] = float_round(dept_totals['TOTAL NETO A PAGAR'] + total_neto, precision_digits=precision)

                for rule in info.get('incomes_name'):
                    amount = float_round(next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0.0), precision_digits=precision)
                    dept_totals[rule] = float_round(dept_totals[rule] + amount, precision_digits=precision)

                for rule in info.get('deductions_name'):
                    amount = float_round(next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0.0), precision_digits=precision)
                    dept_totals[rule] = float_round(dept_totals[rule] + amount, precision_digits=precision)

                # Escribir datos del empleado
                sheet.write(row, 0, emp_count, count_format)
                sheet.write(row, 1, employee.get('entry_date'), money_format)
                sheet.write(row, 2, employee.get('identity'), money_format)
                sheet.write(row, 3, employee.get('bank_account') or '', money_format)
                sheet.write(row, 4, employee.get('employee'), money_format)
                sheet.write(row, 5, employee.get('job') or '', money_format)

                col = 6
                for rule in info.get('incomes_name'):
                    amount = float_round(next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0.0), precision_digits=precision)
                    if amount == 0:
                        sheet.write(row, col, '', money_format)
                    else:
                        sheet.write_number(row, col, amount, money_format)
                    col += 1

                sheet.write_number(row, col, total_devengado, total_totals_format)
                col += 1

                for rule in info.get('deductions_name'):
                    amount = abs(float_round(next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0.0), precision_digits=precision))
                    if amount == 0:
                        sheet.write(row, col, '', money_format)
                    else:
                        sheet.write_number(row, col, amount, money_format)
                    col += 1
                sheet.write_number(row, col, total_deducciones, total_totals_format)
                col += 1

                sheet.write_number(row, col, total_neto, money_format)

                row += 1
                emp_count += 1

            # Escribir totales del departamento
            sheet.merge_range('A%s:F%s'%(row+1,row+1), department_name, dept_name_format)
            col = 6
            for key in headers[6:]:
                dept_val = float_round(abs(dept_totals[key]), precision_digits=precision)
                sheet.write_number(row, col, dept_val, totals_format)
                grand_totals[key] = float_round(grand_totals[key] + dept_totals[key], precision_digits=precision)
                col += 1
            row += 1

        # Gran total general en la última fila
        row += 3
        sheet.merge_range('A%s:F%s'%(row+1,row+1), 'GRAN TOTAL GENERAL', dept_name_format)
        col = 6
        for key in headers[6:]:
            grand_val = float_round(abs(grand_totals[key]), precision_digits=precision)
            sheet.write_number(row, col, grand_val, total_totals_format)
            col += 1

    def get_data(self, docids):
        if len(docids) > 1:
            raise ValidationError('Solo puede imprimir un registro a la vez')

        departments_dict = {}
        deductions_name = []
        incomes_name = []

        deductions_sequence = {}
        incomes_sequence = {}

        payslips = self.env['hr.payslip'].search([('payslip_run_id', 'in', docids)])
        payslip_name = ''
        for payslip in payslips:
            department_name = payslip.employee_id.department_id.name
            deductions = []
            incomes = []
            payslip_name = payslip.payslip_run_id.name

            if 'Salario Mensual' not in incomes_name:
                incomes_name.append('Salario Mensual')
                incomes_sequence['Salario Mensual'] = 1

            if 'Salario Quincenal' not in incomes_name:
                incomes_name.append('Salario Quincenal')
                incomes_sequence['Salario Quincenal'] = 2

            fortnight_amount = payslip.employee_id.wage
            if payslip.worked_days_line_ids:
                line_id = payslip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code == 'WORK100')
                if line_id:
                    fortnight_amount = line_id.amount
            else:
                line_id = payslip.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BASIC')
                if line_id:
                    fortnight_amount = line_id.total

            wage_amount = payslip.employee_id.wage * 2
            if len(payslip.employee_id.historical_salaries_ids) > 0:
                lines = payslip.employee_id.historical_salaries_ids.sorted(
                    key=lambda l: l.end_date_payroll or fields.Date.max
                )

                for line in lines:
                    if payslip.date_to <= line.end_date_payroll:
                        wage_amount = line.amount
                        fortnight_amount = line.amount / 2
                        break

            # Redondear montos base al agregarlos
            incomes.append({'rule_name': 'Salario Quincenal', 'amount': float_round(fortnight_amount, precision_digits=2), 'code': 'SQ', 'sequence': 1})
            incomes.append({'rule_name': 'Salario Mensual', 'amount': float_round(wage_amount, precision_digits=2), 'code': 'SM', 'sequence': 2})
            
            if payslip.worked_days_line_ids and payslip.use_worked_day_lines:
                for entry in payslip.worked_days_line_ids:
                    if entry.work_entry_type_id.code in ['WORK100','OUT']:
                        continue

                    if entry.work_entry_type_id.code == 'OVERTIME' and 'Horas 25%' not in incomes_name:
                        incomes_name.append('Horas 25%')
                        incomes.append({'rule_name': 'Horas 25%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT25'})
                        incomes_sequence['Horas 25%'] = 4

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 5

                    elif entry.work_entry_type_id.code == 'OVERTIME' and 'Horas 25%' in incomes_name:
                        incomes.append({'rule_name': 'Horas 25%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT25'})
                        incomes_sequence['Horas 25%'] = 4

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 5

                    if entry.work_entry_type_id.code == 'OVERTIME50' and 'Horas 50%' not in incomes_name:
                        incomes_name.append('Horas 50%')
                        incomes.append({'rule_name': 'Horas 50%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT50'})
                        incomes_sequence['Horas 50%'] = 6

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 7

                    elif entry.work_entry_type_id.code == 'OVERTIME50' and 'Horas 50%' in incomes_name:
                        incomes.append({'rule_name': 'Horas 50%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT50'})
                        incomes_sequence['Horas 50%'] = 6

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 7

                    if entry.work_entry_type_id.code == 'OVERTIME75' and 'Horas 75%' not in incomes_name:
                        incomes_name.append('Horas 75%')
                        incomes.append({'rule_name': 'Horas 75%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT75'})
                        incomes_sequence['Horas 75%'] = 8

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 9

                    elif entry.work_entry_type_id.code == 'OVERTIME75' and 'Horas 75%' in incomes_name:
                        incomes.append({'rule_name': 'Horas 75%', 'amount': float_round(entry.number_of_hours, precision_digits=2), 'code': 'EXT75'})
                        incomes_sequence['Horas 75%'] = 8

                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': float_round(entry.amount, precision_digits=2), 'code': entry.work_entry_type_id.code})
                        incomes_sequence[entry.work_entry_type_id.name] = 9

                    if entry.work_entry_type_id.name not in incomes_name:
                        incomes_name.append(entry.work_entry_type_id.name)
                        if entry.work_entry_type_id.code == 'OVERTIME':
                            incomes_sequence['Horas 25%'] = 5
                        elif entry.work_entry_type_id.code == 'OVERTIME50':
                            incomes_sequence['Horas 50%'] = 7
                        elif entry.work_entry_type_id.code == 'OVERTIME75':
                            incomes_sequence['Horas 75%'] = 9

            for line in payslip.line_ids:
                if line.total != 0:
                    line_total_rounded = float_round(line.total, precision_digits=2)
                    if line.category_id.code == 'ALW':
                        rule_name = line.salary_rule_id.name
                        sequence = line.salary_rule_id.sequence

                        if rule_name not in incomes_name:
                            incomes_name.append(rule_name)
                            incomes_sequence[rule_name] = sequence

                        domain = [
                            ('payslip_date_from', '<=', payslip.date_from),
                            ('payslip_date_to', '>=', payslip.date_to),
                            ('employee_id', '=', payslip.employee_id.id),
                            ('state', '=', 'finalized')
                        ]
                        mark_id = self.env['hr.employee.attendance.record'].search(domain)
                        if mark_id:
                            if line.salary_rule_id.code == 'HEF':
                                if not any(income['code'] == 'HEFF' for income in incomes):
                                    if 'Cant. Horas Extra Feriado' not in incomes_name:
                                        incomes_name.append('Cant. Horas Extra Feriado')

                                    incomes_sequence['Cant. Horas Extra Feriado'] = sequence - 1

                                    incomes.append({
                                        'rule_name': 'Cant. Horas Extra Feriado',
                                        'amount': float_round(mark_id.eh_holiday_extra, precision_digits=2),
                                        'code': 'HEFF'
                                    })

                            if line.salary_rule_id.code == 'HF':
                                if not any(income['code'] == 'HFF' for income in incomes):
                                    if 'Cant. Dias Feriado' not in incomes_name:
                                        incomes_name.append('Cant. Dias Feriado')

                                    incomes_sequence['Cant. Dias Feriado'] = sequence - 1

                                    incomes.append({
                                        'rule_name': 'Cant. Dias Feriado',
                                        'amount': float_round(mark_id.eh_holiday / 8.0, precision_digits=2),
                                        'code': 'HFF'
                                    })

                        incomes.append({'rule_name': line.salary_rule_id.name, 'amount': line_total_rounded, 'code': line.salary_rule_id.code})

                    if line.category_id.code == 'DED':
                        rule_name = line.salary_rule_id.name
                        sequence = line.salary_rule_id.sequence

                        if rule_name not in deductions_name:
                            deductions_name.append(rule_name)
                            deductions_sequence[rule_name] = sequence
                        deductions.append({'rule_name': line.salary_rule_id.name, 'amount': line_total_rounded, 'code': line.salary_rule_id.code})

            net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
            net_amount = net_line.total if net_line else (payslip.net_wage or 0.0)

            employee_vals = {
                'contract_init_date': payslip.employee_id.contract_date_start,
                'entry_date': payslip.employee_id.contract_date_start.strftime('%d/%m/%Y'),
                'identity': payslip.employee_id.identification_id,
                'bank_account': payslip.employee_id.bank_account_ids.acc_number,
                'employee': payslip.employee_id.name,
                'job': payslip.employee_id.job_id.name,
                'monthly_salary': float_round(payslip.employee_id.wage * 2, precision_digits=2),
                'level': int(payslip.employee_id.level_number),
                'salary': float_round(payslip.employee_id.wage, precision_digits=2),
                'deductions': deductions,
                'incomes': incomes,
                'net_amount': float_round(net_amount, precision_digits=2),
            }

            if department_name not in departments_dict:
                departments_dict[department_name] = {'employees': [], 'level': payslip.employee_id.department_id.priority_level,}
            departments_dict[department_name]['employees'].append(employee_vals)

            for department in departments_dict.values():
                department['employees'].sort(
                    key=lambda e: (
                        e['level'] or 0,
                        e['contract_init_date'] or fields.Date.today()
                    )
                )

        departments_dict = OrderedDict(
            sorted(
                departments_dict.items(),
                key=lambda item: item[1]['level'] or 0
            )
        )

        incomes_name.sort(
            key=lambda name: incomes_sequence.get(name, 9999)
        )

        deductions_name.sort(
            key=lambda name: deductions_sequence.get(name, 9999)
        )

        return {'department_data': departments_dict, 'deductions_name': deductions_name, 'incomes_name': incomes_name, 'payslip_name': payslip_name}