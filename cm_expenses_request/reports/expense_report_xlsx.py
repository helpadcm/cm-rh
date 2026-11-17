# -*- coding: utf-8 -*-
from odoo import models, _

class ExpenseReportXlsx(models.AbstractModel):
    _name = 'report.cm_reports_cobus.report_expense_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Reporte de Viáticos por Departamento"

    def generate_xlsx_report(self, workbook, data, wizards):
        sheet = workbook.add_worksheet('Reporte de Viáticos')
        
        wizard = wizards[0]
        date_from = wizard.date_from
        date_to = wizard.date_to
        selected_departments = wizard.department_ids
        selected_state = wizard.state

        format_title = workbook.add_format({'font_size': 13, 'align': 'center', 'valign': 'vcenter', 'bold': True})
        format_date = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bold': True})
        
        format_dept_header = workbook.add_format({'font_size': 11, 'align': 'left', 'bold': True, 'color': '#1f4e78'})
        format_table_header = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#eaeaea', 'border': 1})
        
        format_center = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1})
        format_amount = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1, 'num_format': 'L #,##0.00'})
        
        format_total_label = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True, 'border': 1, 'bg_color': '#f2f2f2'})
        format_total_value = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True, 'border': 1, 'num_format': 'L #,##0.00', 'bg_color': '#f2f2f2'})

        sheet.set_column(0, 0, 4)
        sheet.set_column(1, 1, 16)
        sheet.set_column(2, 2, 22)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 28)
        sheet.set_column(5, 5, 28)
        sheet.set_column(6, 6, 18)

        pos = 1

        sheet.merge_range("B1:G1", _('REPORTE DE VIÁTICOS - POR DEPARTAMENTO'), format_title)
        sheet.merge_range("B2:G2", _('Desde: %s    Al: %s') % (date_from, date_to), format_date)
        
        pos += 2

        domain = [
            ('date', '>=', str(date_from)),
            ('date', '<=', str(date_to))
        ]
        
        if selected_departments:
            domain.append(('department_id', 'in', selected_departments.ids))

        if selected_state:
            domain.append(('state', '=', selected_state))

        requests = self.env['cm.expenses.request'].search(domain)

        grouped_data = {}
        for req in requests:
            dept_name = req.department_id.name if req.department_id else 'SIN DEPARTAMENTO'
            
            if dept_name not in grouped_data:
                grouped_data[dept_name] = []
            
            req_name = req.name if hasattr(req, 'name') and req.name else ''
            process_name = req.process_id.name if hasattr(req, 'process_id') and req.process_id else ''
            assign_to = req.assign_to_id.name if hasattr(req, 'assign_to_id') and req.assign_to_id else ''
            employee = req.employee_id.name if hasattr(req, 'employee_id') and req.employee_id else ''
            advance = req.advance_amount if hasattr(req, 'advance_amount') else 0.0

            grouped_data[dept_name].append({
                'name': req_name,
                'process': process_name,
                'date': str(req.date) if req.date else '',
                'assign_to': assign_to,
                'employee': employee,
                'advance_amount': advance
            })

        for dept, items in grouped_data.items():
            sheet.write(pos, 1, dept.upper(), format_dept_header)
            pos += 1

            sheet.write(pos, 1, _('Nombre'), format_table_header)
            sheet.write(pos, 2, _('Proceso'), format_table_header)
            sheet.write(pos, 3, _('Fecha de Solicitud'), format_table_header)
            sheet.write(pos, 4, _('Asignado a'), format_table_header)
            sheet.write(pos, 5, _('Solicitado por'), format_table_header)
            sheet.write(pos, 6, _('Anticipo al Empleado'), format_table_header)
            pos += 1

            total_advance = 0.0
            for item in items:
                sheet.write(pos, 1, item['name'], format_center)
                sheet.write(pos, 2, item['process'], format_center)
                sheet.write(pos, 3, item['date'], format_center)
                sheet.write(pos, 4, item['assign_to'], format_center)
                sheet.write(pos, 5, item['employee'], format_center)
                sheet.write(pos, 6, item['advance_amount'], format_amount)
                
                total_advance += item['advance_amount']
                pos += 1

            sheet.write(pos, 5, _('TOTAL DEPARTAMENTO'), format_total_label)
            sheet.write(pos, 6, total_advance, format_total_value)
            
            pos += 2
