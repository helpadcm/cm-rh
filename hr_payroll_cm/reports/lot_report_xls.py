from odoo import models
import base64
import io

class lotFormatXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_cm.lot_format_cm_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Formato de nomina XLS"

    def generate_xlsx_report(self, workbook, data, docids):
        info = self.get_data(docids.ids)
        sheet = workbook.add_worksheet('Planilla')

        # Obtener la empresa y el logo
        company = self.env.user.company_id
        if company.logo:
            image_data = io.BytesIO(base64.b64decode(company.logo))  # Decodificar logo
            sheet.insert_image('A1', 'logo.png', {'image_data': image_data, 'x_scale': 0.2, 'y_scale': 0.15})  # Ajustar tamaño


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
        grand_totals = {name: 0 for name in headers[6:]}  # Acumulador para gran total

        # Iterar sobre departamentos y empleados agrupados
        for department_name, department_info in info.get('department_data').items():
            dept_totals = {name: 0 for name in headers[6:]}  # Acumulador para cada departamento

            for employee in department_info.get('employees'):
                salario_quincenal = employee.get('salary')
                total_ingresos = sum(x['amount'] for x in employee.get('incomes') if x.get('code') not in ['EXT','SM'] )
                total_devengado = total_ingresos  # **CORREGIDO**
                total_deducciones = abs(sum(x['amount'] for x in employee.get('deductions')))
                total_neto = total_devengado - total_deducciones

                # Acumular valores al total del departamento
                dept_totals['Total Devengado'] += total_devengado
                dept_totals['Total Deducciones'] += total_deducciones
                dept_totals['TOTAL NETO A PAGAR'] += total_neto

                for rule in info.get('incomes_name'):
                    amount = next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0)
                    dept_totals[rule] += amount

                for rule in info.get('deductions_name'):
                    amount = next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0)
                    dept_totals[rule] += amount

                # Escribir datos del empleado
                sheet.write(row, 0, emp_count, count_format)
                sheet.write(row, 1, employee.get('entry_date'), money_format)
                sheet.write(row, 2, employee.get('identity'), money_format)
                sheet.write(row, 3, employee.get('bank_account') or '', money_format)
                sheet.write(row, 4, employee.get('employee'), money_format)
                sheet.write(row, 5, employee.get('job') or '', money_format)
                # sheet.write_number(row, 6, employee.get('monthly_salary'), money_format)
                # sheet.write_number(row, 7, salario_quincenal, money_format)

                col = 6
                for rule in info.get('incomes_name'):
                    amount = next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0)
                    if amount == 0:
                        sheet.write(row, col, '', money_format)
                    else:
                        sheet.write_number(row, col, amount, money_format)
                    col += 1

                sheet.write_number(row, col, total_devengado, total_totals_format)  # **CORREGIDO**
                col += 1

                for rule in info.get('deductions_name'):
                    amount = abs(next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0))
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
            # sheet.write(row, 0, department_name, dept_format)
            col = 6
            for key in headers[6:]:
                sheet.write_number(row, col, abs(dept_totals[key]), totals_format)
                grand_totals[key] += dept_totals[key]  # Acumulamos en el gran total general
                col += 1
            row += 1

        # Gran total general en la última fila
        row+=3
        sheet.merge_range('A%s:F%s'%(row+1,row+1), 'GRAN TOTAL GENERAL', dept_name_format)
        col = 6
        for key in headers[6:]:
            sheet.write_number(row, col, grand_totals[key], total_totals_format)
            col += 1
            

    def get_data(self, docids):
        if len(docids) > 1:
            raise ValidationError('Solo puede imprimir un registro a la vez')

        departments_dict = {}
        deductions_name = []
        incomes_name = []

        payslips = self.env['hr.payslip'].search([('payslip_run_id', 'in', docids)])
        payslip_name = ''
        for payslip in payslips:
            department_name = payslip.employee_id.department_id.name
            deductions = []
            incomes = []
            payslip_name = payslip.payslip_run_id.name

            if 'Salario Mensual' not in incomes_name:
                incomes_name.append('Salario Mensual')

            if 'Salario Quincenal' not in incomes_name:
                incomes_name.append('Salario Quincenal')

            if payslip.worked_days_line_ids:
                fortnight_amount = payslip.employee_id.wage
                line_id = payslip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code == 'WORK100')
                if line_id:
                    fortnight_amount = line_id.amount
            else:
                line_id = payslip.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BASIC')
                if line_id:
                    fortnight_amount = line_id.total

            wage_amount = payslip.employee_id.wage * 2
            if len(payslip.employee_id.historical_salaries_ids) > 0:
                # for line in payslip.employee_id.historical_salaries_ids:
                #     if (line.start_date_payroll 
                #     and line.start_date_payroll <= payslip.date_to 
                #     and (not line.end_date_payroll or payslip.date_to <= line.end_date_payroll)):
                #         print ("?????????????????????????????????")
                #         print (payslip.employee_id.name)
                #         print (payslip.date_to, line.end_date_payroll)
                #         wage_amount = line.amount
                #         fortnight_amount = line.amount / 2
                lines = payslip.employee_id.historical_salaries_ids.sorted(
                    key=lambda l: l.end_date_payroll or fields.Date.max
                )

                found = False

                for line in lines:
                    if payslip.date_to <= line.end_date_payroll:
                        wage_amount = line.amount
                        fortnight_amount = line.amount / 2
                        found = True
                        break

                # 🔥 fallback: usar el último salario
                # if not found and lines:
                #     wage_amount = lines[-1].amount
                #     fortnight_amount = wage_amount / 2

            incomes.append({'rule_name': 'Salario Quincenal', 'amount': fortnight_amount, 'code': 'SQ'})
            incomes.append({'rule_name': 'Salario Mensual', 'amount': wage_amount, 'code': 'SM'})
            
            if payslip.worked_days_line_ids and payslip.use_worked_day_lines:
                for entry in payslip.worked_days_line_ids:
                    if entry.work_entry_type_id.code != 'WORK100':
                        if entry.work_entry_type_id.code == 'OVERTIME' and 'Horas Extra' not in incomes_name:
                            incomes_name.append('Horas Extra')
                            incomes.append({'rule_name': 'Horas Extra', 'amount': entry.number_of_hours, 'code': 'EXT'})
                        elif entry.work_entry_type_id.code == 'OVERTIME' and 'Horas Extra' in incomes_name:
                            incomes.append({'rule_name': 'Horas Extra', 'amount': entry.number_of_hours, 'code': 'EXT'})

                        if entry.work_entry_type_id.name not in incomes_name:
                            incomes_name.append(entry.work_entry_type_id.name)
                        
                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': entry.amount, 'code': entry.work_entry_type_id.code})

            for line in payslip.line_ids:
                if line.category_id.code == 'ALW':
                    if line.salary_rule_id.name not in incomes_name:
                        incomes_name.append(line.salary_rule_id.name)
                    incomes.append({'rule_name': line.salary_rule_id.name, 'amount': line.total, 'code': line.salary_rule_id.code})

                if line.category_id.code == 'DED':
                    if line.salary_rule_id.name not in deductions_name:
                        deductions_name.append(line.salary_rule_id.name)
                    deductions.append({'rule_name': line.salary_rule_id.name, 'amount': line.total, 'code': line.salary_rule_id.code})

            employee_vals = {
                'entry_date': payslip.employee_id.contract_date_start.strftime('%d/%m/%Y'),
                'identity': payslip.employee_id.identification_id,
                'bank_account': payslip.employee_id.bank_account_ids.acc_number,
                'employee': payslip.employee_id.name,
                'job': payslip.employee_id.job_id.name,
                'monthly_salary': payslip.employee_id.wage * 2,
                'salary': payslip.employee_id.wage,
                'deductions': deductions,
                'incomes': incomes
            }

            if department_name not in departments_dict:
                departments_dict[department_name] = {'employees': []}
            departments_dict[department_name]['employees'].append(employee_vals)

        return {'department_data': departments_dict, 'deductions_name': deductions_name, 'incomes_name': incomes_name, 'payslip_name': payslip_name}