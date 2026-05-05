# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields,_
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class ledgerAnalyticAccount(models.AbstractModel):
    _name = 'report.core_report_xls.ledger_analytic_account_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Libro Mayor Cuentas Analiticas"
	
    def generate_xlsx_report(self, workbook, data, lines): 	
        xlines = self.get_data(data)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'text_wrap': True, 'bold': False})
        format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format212 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#CDCDCD'})
        {}
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.00'})
        format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.00', 'bg_color': '#dadada'})
        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': '#,###,##0.00'})
        format43 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00'})
        format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format511 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                    'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')

        #########TITULOS
        sheet.merge_range('A1:I1', _('Detalle de Cuentas Analiticas'), format1)
        datax={}
            
        sheet.merge_range('A3:C3', _('Cuentas'), format211)
        if not data.get('account_ids'):
            sheet.merge_range('A4:C4', _('Todas'), format21)
        else:
            account_ids = self.env['account.account'].search([('id','in',data['account_ids'])])
            account_name = ','.join([account.name for account in account_ids])
            sheet.merge_range('A4:C4', account_name, format21)
        
        sheet.merge_range('D3:E3', _('Analiticas'), format211)
        if not data.get('analytic_account_ids'):
            sheet.merge_range('D4:E4', _('Todas'), format21)
        else:
            account_analytic_ids = self.env['account.analytic.account'].search([('id','in',data['analytic_account_ids'])])
            analytic_name = ','.join([analytic.name for analytic in account_analytic_ids])
            sheet.merge_range('D4:E4', analytic_name, format21)

        sheet.merge_range('F3:G3', _('Contactos'), format211)
        if not data.get('partner_ids'):
            sheet.merge_range('F4:G4', _('Todos'), format21)
        else:
            partner_ids = self.env['res.partner'].search([('id','in',data['partner_ids'])])
            partner_name = ','.join([p.name for p in partner_ids])
            sheet.merge_range('F4:G4', partner_name, format21)

        if data.get('group_by'):
            if data.get('group_by') == 'analytic':
                group_name = 'Cuenta Analitica'
            elif data.get('group_by') == 'partner':
                group_name = 'Contacto'
            elif data.get('group_by') == 'account':
                group_name = 'Cuenta Contable'
            else:
                group_name = 'Ninguno'

            sheet.write(2, 8, _('Agrupado por'), format211)
            sheet.write(3, 8, group_name, format21)

        if data.get('initial_date'):
            sheet.write(2, 9, _('Fecha Inicio'), format211)
            sheet.write(3, 9, data['initial_date'], format21)

        if data.get('final_date'):
            sheet.write(2, 10, _('Fecha Fin'), format211)
            sheet.write(3, 10, data['final_date'], format21)

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 50)
        sheet.set_column(4, 4, 35)
        sheet.set_column(5, 5, 35)
        sheet.set_column(6, 6, 35)
        sheet.set_column(7, 7, 35)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        pos=5

        pos+=1
        if data.get('group_by'):
            for line in xlines:
                title_analytic = "A" + str(pos + 1) + ":" + "C" + str(pos + 1)
                sheet.merge_range(title_analytic, line.get('group_name'), format212)
                pos += 1
                sheet.write(pos, 0, _('No.'), format211)
                sheet.write(pos, 1, _('Fecha'), format211)
                sheet.write(pos, 2, _('Movimiento'), format211)
                sheet.write(pos, 3,_('Ref'), format211)
                sheet.write(pos, 4,_('Contacto'), format211)
                sheet.write(pos, 5, _('Analitica'), format211)
                sheet.write(pos, 6, _('Cuenta Contable'), format211)
                sheet.write(pos, 7, _('Cuenta Prespuestaria'), format211)
                sheet.write(pos, 8, _('Porcentaje'), format211)
                sheet.write(pos, 9, _('Monto'), format211)
                sheet.write(pos, 10, _('Monto Linea'), format211)
                pos += 1
                cont = 1
                total_1 = 0
                total_2 = 0
                for data in line.get('values'):
                    sheet.write(pos, 0, cont, format21)
                    sheet.write(pos, 1, data.get('date').strftime('%d/%m/%Y'), format21)
                    sheet.write(pos, 2, data.get('move_name'), format21)
                    sheet.write(pos, 3, data.get('name'), format21)
                    sheet.write(pos, 4, data.get('partner_name'), format21)
                    sheet.write(pos, 5, data.get('analytic_account_name'), format21)
                    sheet.write(pos, 6, data.get('account_name'), format21)
                    sheet.write(pos, 7, data.get('budget_account_name'), format21)
                    sheet.write(pos, 8, f"""{(data.get('percentage'))}%""", format21)
                    sheet.write_number(pos, 9, data.get('analytic_amount'), format41)
                    sheet.write_number(pos, 10, data.get('line_total'), format41)
                    total_1 += data.get('analytic_amount')
                    total_2 += data.get('line_total')
                    cont += 1
                    pos += 1
                sheet.write(pos, 8, "TOTAL", format212)
                sheet.write_number(pos, 9, total_1, format411)
                sheet.write_number(pos, 10, total_2, format411)
                pos += 2
        else:
            sheet.write(pos, 0, _('No.'), format211)
            sheet.write(pos, 1, _('Fecha'), format211)
            sheet.write(pos, 2, _('Movimiento'), format211)
            sheet.write(pos, 3,_('Ref'), format211)
            sheet.write(pos, 4,_('Contacto'), format211)
            sheet.write(pos, 5, _('Analitica'), format211)
            sheet.write(pos, 6, _('Cuenta Contable'), format211)
            sheet.write(pos, 7, _('Cuenta Prespuestaria'), format211)
            sheet.write(pos, 8, _('Porcentaje'), format211)
            sheet.write(pos, 9, _('Monto'), format211)
            sheet.write(pos, 10, _('Monto Linea'), format211)
            pos += 1
            total_1 = 0
            total_2 = 0
            cont = 1
            for line in xlines:
                for data in line.get('values'):
                    sheet.write(pos, 0, cont, format21)
                    sheet.write(pos, 1, data.get('date').strftime('%d/%m/%Y'), format21)
                    sheet.write(pos, 2, data.get('move_name'), format21)
                    sheet.write(pos, 3, data.get('name'), format21)
                    sheet.write(pos, 4, data.get('partner_name'), format21)
                    sheet.write(pos, 5, data.get('analytic_account_name'), format21)
                    sheet.write(pos, 6, data.get('account_name'), format21)
                    sheet.write(pos, 7, data.get('budget_account_name'), format21)
                    sheet.write(pos, 8, f"""{(data.get('percentage'))}%""", format21)
                    sheet.write_number(pos, 9, data.get('analytic_amount'), format41)
                    sheet.write_number(pos, 10, data.get('line_total'), format41)
                    total_1 += data.get('analytic_amount')
                    total_2 += data.get('line_total')
                    cont += 1
                    pos += 1
            sheet.write(pos, 8, "TOTAL", format212)
            sheet.write_number(pos, 9, total_1, format411)
            sheet.write_number(pos, 10, total_2, format411)
            pos += 2

    def get_data(self,data):
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')
        analytic_account_ids = data.get('analytic_account_ids')
        account_ids = data.get('account_ids')
        partner_ids = data.get('partner_ids')
        group_by = data.get('group_by')
        query = """
        SELECT
            am.internal_number AS move_name,
            aa.id AS account_id,
            partner.id AS partner_id,
            aml.date,
            aml.name,
            aa.name->>'es_CR' AS account_name,
            aml.balance AS line_total,
            aml.debit,
            aml.credit,
            aaa.id AS analytic_account_id,
            aaa.name->>'es_CR' AS analytic_account_name,
            (dist.value::float) AS percentage,
            aml.balance * (dist.value::float / 100) AS analytic_amount,
            partner.name AS partner_name,
            budget_account.name AS budget_account_name
        FROM account_move_line aml
        JOIN account_move am ON am.id = aml.move_id
        JOIN account_account aa ON aa.id = aml.account_id
        JOIN account_budget_account budget_account ON budget_account.id = aml.analytic_account_id
        JOIN res_partner partner ON aml.partner_id = partner.id
        JOIN LATERAL jsonb_each_text(aml.analytic_distribution) AS dist(key, value) ON TRUE
        JOIN account_analytic_account aaa ON aaa.id = dist.key::int
        WHERE aml.parent_state = 'posted'
            AND am.move_type in ('entry','in_invoice')
            AND aml.date BETWEEN %s AND %s
            AND aml.analytic_distribution IS NOT NULL
            AND aml.analytic_distribution != '{}'
        """

        params = [initial_date, final_date]
        if account_ids:
            query += " AND aml.account_id IN %s"
            params.append(tuple(account_ids))

        if analytic_account_ids:
            query += " AND aaa.id IN %s"
            params.append(tuple(analytic_account_ids))
        
        if partner_ids:
            query += " AND aml.partner_id IN %s"
            params.append(tuple(partner_ids))

        self.env.cr.execute(query, tuple(params))
        result = self.env.cr.dictfetchall()
        info = []
        group_ids = []
        for row in result:
            if group_by == 'analytic':
                group_id = row.get('analytic_account_id')
                group_name = row.get('analytic_account_name')
            elif group_by == 'partner':
                group_id = row.get('partner_id')
                group_name = row.get('partner_name')
            elif group_by == 'account':
                group_id = row.get('account_id')
                group_name = row.get('account_name')

            if group_by:
                if group_id in group_ids:
                    info[group_ids.index(group_id)]['values'].append(row)
                else:
                    group_ids.append(group_id)
                    info.append({
                        'group_name': group_name,
                        'values': [row]
                    })
            else:
                info.append({
                    'values': [row]
                })
        return info

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha