import datetime
from odoo import _, models

class GeneralLegderReport(models.AbstractModel):
	_name = 'report.core_report_xls.report_generalledger_xls'
	_inherit = 'report.report_xlsx.abstract'
	_description = "Reporte de Facturas XLS"
	
	def get_lines(self, data, docids):
		report_ob = self.env.get('report.accounting_pdf_reports.report_general_ledger')
		lines = report_ob.render_xls(docids, data=data)
		return lines
		
	def generate_xlsx_report(self, workbook, data, lines): 	
		xlines = self.get_lines(data, data.get('ids'))
		sheet = workbook.add_worksheet()
		format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
		format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
		format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
		format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
		format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
		{}
		format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.00'})
		format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
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
		sheet.merge_range('A1:L1', _('Libro Mayor'), format1)
		datax={}
		sheet.merge_range('A2:B2', _('Diarios'), format211)
		sheet.merge_range('A3:B4', ', '.join([ lt or '' for lt in xlines['print_journal'] ]), format21)
		datax = xlines.get('data')
		daccount=""
		if datax['display_account']== 'all':
			daccount=_("Todas las cuentas")
		if datax['display_account']== 'movement':
			daccount=_("Con Movimientos")
		if datax['display_account']== 'not_zero':
			daccount=_("Con saldo distinto de cero")
		sheet.write(1, 3, _('Cuentas'), format211)
		sheet.write(2, 3, daccount, format21)

		tmoves=""
		if datax['target_move']== 'all':
			tmoves=_("Todos")
		if datax['target_move']== 'posted':
			tmoves=_("Todos los asientos publicados")

		sheet.write(1, 5, _('Movimientos'), format211)
		sheet.write(2, 5, tmoves, format21)
		
		sortby=""
		if datax['sortby']== 'sort_date':
			sortby=_("Fecha")
		if datax['sortby']== 'sort_journal_partner':
			sortby=_("Diario y Contacto")

		sheet.write(1, 7, _('Ordenar por:'), format211)
		sheet.write(2, 7, sortby, format21)
		groby=""
		if datax['group_ledger']== 'all':
			groby=_("Contacto")
		if datax['group_ledger']== 'posted':
			groby=_("Analitica")

		sheet.write(1, 9, _('Agrupar por:'), format211)
		sheet.write(2, 9, groby, format21)
		
		sheet.merge_range('A5:B5', _('Contactos'), format211)
		if not xlines['partner_ids']:
			sheet.merge_range('A6:B6', _('Todos'), format21)
		else:
			sheet.merge_range('A6:B6', ', '.join([ lt.name or '' for lt in xlines['partner_ids'] ]), format21)
        	
		sheet.merge_range('D5:E5', _('Analiticas'), format211)
		if not xlines['analytic_account_ids']:
			sheet.merge_range('D6:E6', _('Todas'), format21)
		else:
			sheet.merge_range('D6:E6', xlines['analytic_account_ids'], format21)
        		
		if datax.get('date_from'):
			sheet.write(4, 7, _('Fecha Inicio'), format211)
			sheet.write(5, 7, datax['date_from'], format21)
		if datax.get('date_to'):
			sheet.write(4, 9, _('Fecha Fin'), format211)
			sheet.write(5, 9, datax['date_to'], format21)

		sheet.set_column(1, 1, 10)
		sheet.set_column(8, 8, 10)
		sheet.set_column(9,9, 10)
		sheet.set_column(10, 10, 10)
		sheet.set_column(0, 0, 10)
		sheet.set_column(3, 3, 26)
		sheet.set_column(4, 4, 26)
		sheet.set_column(6, 6, 16)
		pos=7
        	#########"TITULOS LINEA"
		sheet.write(pos, 0, _('No.'), format211)
		sheet.write(pos, 1, _('Fecha'), format211)
		sheet.write(pos, 2, _('Diario'), format211)
		sheet.write(pos, 3, _('Contacto'), format211)
		sheet.write(pos, 4, _('Analitica'), format211)
		sheet.write(pos, 5,_('Ref'), format211)
		sheet.write(pos, 6, _('Movimiento'), format211)
		sheet.write(pos, 7, _('Etiqueta'), format211)
		sheet.write(pos, 8,_('Debito'), format211)
		sheet.write(pos, 9, _('Credito'), format211)
		sheet.write(pos, 10,_('Saldo'), format211)
		
		if self.env.user.has_group('base.group_multi_currency'):
			sheet.write(pos, 11,_('Moneda'), format211)
		pos+=1
		#CUENTAS Y LINEAS DE CUENTA
		for account in xlines.get('Accounts',[]):
			sheet.write(pos, 0, account.get('code'), format211)
			sheet.write(pos, 3, account.get('name'), format211)
			sheet.write(pos, 2, '', format211)
			sheet.write(pos, 1, '', format211)
			sheet.write(pos, 4, '', format211)
			sheet.write(pos, 5, '', format211)
			sheet.write_number(pos, 8,float( account['debit']), format411)
			sheet.write_number(pos, 9, float(account['credit']), format411)
			sheet.write_number(pos, 10, float(account['balance']), format411)
			if self.env.user.has_group('base.group_multi_currency'):
				sheet.write_number(pos, 11, account.get('amount_currency') or 0, format42)
				sheet.write(pos, 12, account.get('currency_code'), format211)
			pos+=1
			
			for line in account['move_lines']:
				if line['lid']>0:
					sheet.write(pos, 0, '', format21)
					sheet.write(pos, 1, line['ldate'], format21)
					sheet.write(pos, 2, line['lcode'], format21)
					sheet.write(pos, 3, line['partner_name'], format21)
					sheet.write(pos, 4, line.get('analytic_name'), format21)
					sheet.write(pos, 5, line['lref'], format21)
					sheet.write(pos, 6, line['move_name'], format21)
					sheet.write(pos, 7, line['lname'], format21)
					sheet.write_number(pos, 8, line['debit'], format41)
					sheet.write_number(pos, 9, line['credit'], format41)
					sheet.write_number(pos, 10, line['balance'], format41)
					if self.env.user.has_group('base.group_multi_currency'):
						sheet.write_number(pos, 11, line.get('amount_currency'), format43)
						sheet.write(pos, 12, line.get('currency_code'), format21)
				if line['lid']==0:
					#negrita
					sheet.write(pos, 1, line['ldate'], format211)
					sheet.write(pos, 2, line['lcode'], format211)
					sheet.write(pos, 3, line['partner_name'], format211)
					sheet.write(pos, 4, line.get('analytic_name'), format211)
					sheet.write(pos, 5, line['lref'], format211)
					sheet.write(pos, 6, line['move_name'], format211)
					sheet.write(pos, 7, line['lname'], format211)
					if xlines.get('init_balance')==1:
						sheet.write_number(pos, 8, line['debit'], format411)
						sheet.write_number(pos, 9, line['credit'], format411)
						sheet.write_number(pos, 10, line['balance'], format411)
						if self.env.user.has_group('base.group_multi_currency'):
							sheet.write_number(pos, 11, line.get('amount_currency'), format42)
							sheet.write(pos, 12, line.get('currency_code'), format211)
				if line['lid']==-1:
					#negrita
					sheet.write(pos, 1, line['ldate'], format211)
					sheet.write(pos, 2, line['lcode'], format211)
					sheet.write(pos, 3, line['partner_name'], format211)
					sheet.write(pos, 4, line.get('analytic_name'), format211)
					sheet.write(pos, 5, line['lref'], format211)
					sheet.write(pos, 6, line['move_name'], format211)
					sheet.write(pos, 7, line['lname'], format211)
					sheet.write_number(pos, 8, line['debit'], format411)
					sheet.write_number(pos, 9, line['credit'], format411)
					sheet.write_number(pos, 10, line['balance'], format411)
					if self.env.user.has_group('base.group_multi_currency'):
						sheet.write_number(pos, 11, line.get('amount_currency'), format42)
						sheet.write(pos, 12, line.get('currency_code'), format211)
				pos+=1
