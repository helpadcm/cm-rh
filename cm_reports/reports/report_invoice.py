# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields, _
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ReportBook(models.AbstractModel):
	_name = 'report.cm_reports.general_invoice'
	_description = "Reporte general de facturas"

	@api.model
	def render_xls(self, docids, data=None):
		res = {}
		if data.get('report_type') == u'xlsx':
			docids = docids.ids
		else:
			docids=None
		
		obj_history=self.env['account.move']
		if not docids:
			docids = self.get_ids(data.get('form',{}))
		
		tfo = data.get('form',{})
		symbol2 = self.env.user.company_id.currency_id.symbol
		
		data2 = self.with_context(tfo).get_data(docids)
		type_of = tfo.get('type_of')
		type_contact = ''
		if tfo.get('type_of') == 'out_invoice':
			type_contact = 'Cliente'
		if tfo.get('type_of') == 'in_invoice':
			type_contact = 'Proveedor'

		group_by = ''
		if tfo.get('group_ledger') == 'partner':
			group_by = 'Contacto'
		elif tfo.get('group_ledger') == 'month':
			group_by = 'Fecha'
		elif tfo.get('group_ledger') == 'partner_month':
			group_by = 'Contacto y Fecha'
		elif tfo.get('group_ledger') == 'month_partner':
			group_by = 'Fecha y Contacto'
		tfo.update({'type_of': type_contact})
		tfo.update({'group_ledger': group_by})

		docargs = {
			'type_of': type_of,
			'option': tfo,
			'doc_ids': docids,
			'doc_model': obj_history,
			'data': data2,
			'symbol': symbol2,
			'docs': obj_history.browse(docids),
			'time': time,
		}
		return docargs

	@api.model
	def _get_report_values(self, docids, data=None):
		res = {}
		obj_history=self.env['account.move']
		if not docids:
			docids = self.get_ids(data.get('form',{}))
		
		tfo = data.get('form',{})
		symbol2 = self.env.user.company_id.currency_id.symbol#self.env.get('res.company').browse(tfo.get('company_id')[0]).currency_id.symbol
		data2 = self.with_context(tfo).get_data(docids)
		type_of = tfo.get('type_of')
		type_contact = ''
		if tfo.get('type_of') == 'out_invoice':
			type_contact = 'Cliente'
		if tfo.get('type_of') == 'in_invoice':
			type_contact = 'Proveedor'

		group_by = ''
		if tfo.get('group_ledger') == 'partner':
			group_by = 'Contacto'
		elif tfo.get('group_ledger') == 'month':
			group_by = 'Fecha'
		elif tfo.get('group_ledger') == 'partner_month':
			group_by = 'Contacto y Fecha'
		elif tfo.get('group_ledger') == 'month_partner':
			group_by = 'Fecha y Contacto'
		tfo.update({'type_of': type_contact})
		tfo.update({'group_ledger': group_by})
		
		docargs = {
			'type_of':type_of,
			'option':tfo,
			'doc_ids': docids,
			'doc_model': obj_history,
			'data': data2,
			'symbol':symbol2,
			'docs': obj_history.browse(docids),
			'time': time,
		}
		return docargs

	def get_ids(self,data):
		obj_history = self.env['account.move']
		domain = [('state','not in',['draft'])]
		partner_ids = data.get('partner_ids',[])
		type_o = data.get('type_of',False)
		date_to = data.get('date_to')
		date_from = data.get('date_from')
		company_id = data.get('company_id')
		if type_o:
			domain.append(['move_type','=',type_o])
		if date_to:
			date = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
			domain.append(['date','<=',date_to])
		if date_from:
			date = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
			domain.append(['date','>=',date_from])
		if len(partner_ids)>0:
			domain.append(['partner_id','in',partner_ids])
		if company_id:
			domain.append(['company_id','=',company_id[0]])
		ids = obj_history.search(domain).ids
		return ids

	def get_mes(self,date):
		a = datetime.strptime(str(date), DEFAULT_SERVER_DATE_FORMAT)
		res= "%02.f/%s"%(a.month,str(a.year))
		return res

	def get_taxes(self, invoice):
		valisv_15 = 0
		valisv_18 = 0
		amount_0 = 0
		amount_15 = 0
		amount_18 = 0
		for line in invoice.invoice_line_ids:
			if len(line.tax_ids) == 0:
				amount_0 += line.price_subtotal
			else:
				for tax in line.tax_ids:
					base_amount = line.price_subtotal
					tax_results = line.tax_ids.compute_all(base_amount, currency=line.move_id.currency_id, quantity=line.quantity)
					total_tax_amount = tax_results['total_included'] - tax_results['total_excluded']
					if tax.amount == 15:
						amount_15 += base_amount
						valisv_15 += total_tax_amount
					if tax.amount == 18:
						amount_18 += base_amount
						valisv_18 += total_tax_amount
					if tax.amount == 0:
						amount_0 += base_amount
		res={
			'isv_15': valisv_15,
			'isv_18': valisv_18,
			'amount_0': amount_0,
			'amount_15': amount_15,
			'amount_18': amount_18,
			'amount': valisv_15 + valisv_18 + amount_0 + amount_15 + amount_18
		}
		return res

	def get_line(self, invoice, date_format="%d/%m/%Y"):
		taxes=self.get_taxes(invoice)
		rate = self._get_currency(invoice.date, invoice.journal_id)
		if invoice.state == 'cancel':
			rate=0
		
		fdate = datetime.strptime(str(invoice.invoice_date), DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)

		cai = ''
		if invoice.move_type == 'out_invoice':
			cai = invoice.cai_number
		elif invoice.move_type == 'in_invoice':
			cai = invoice.cai_id.name

		res={
			'symbol': invoice.company_id.currency_id.symbol,
			'title_name': invoice.name,
			'name': invoice.name if invoice.move_type == 'out_invoice' else invoice.ref,
			'subtitle_name': invoice.partner_id.name,
			'ref': invoice.name,
			'date': fdate,
			'amount_total': taxes.get('amount')*rate,
			'isv_15': taxes.get('isv_15')*rate,
			'isv_18': taxes.get('isv_18')*rate,
			'amount_0': taxes.get('amount_0')*rate,
			'amount_15': taxes.get('amount_15')*rate,
			'amount_18': taxes.get('amount_18')*rate,
			'cai': cai or '',
			'rtn': invoice.partner_id.vat or '',
			'user_id': invoice.user_id.name,
			'sub': False,
		}
		return res

	def _get_currency(self, date, journal_id):
		date1 = date
		comp_rate = 1
		if journal_id.currency_id:
			user_obj = self.env.user
			if not journal_id.currency_id.id == user_obj.company_id.currency_id.id:
				comp_rate = 1/user_obj.company_id.currency_id._get_conversion_rate(user_obj.company_id.currency_id, journal_id.currency_id, self.env.company, date1)
			else:
				comp_rate = 1/journal_id.currency_id.rate
		return comp_rate

	def get_data(self,docids):
		res=[]
		group_by = self.env.context.get('group_ledger','month_partner')
		lang_code = self.env.context.get('used_context',{}).get('lang') or 'es_ES'
		lang = self.env['res.lang']
		lang= self.env.get('res.lang')
		lang_id = lang._lang_get(lang_code)
		date_format = lang_id.date_format
		show_detail = self.env.context.get('show_detail',True)
		obj_invoice = self.env['account.move']
		month_ids = []
		partner_ids = []
		data = []
		final = []
		month_name = []
		if group_by == 'partner':
			amount_total=0.0
			amount_15=0.0
			isv_15=0.0
			amount_18=0.0
			isv_18=0.0
			amount_0=0.0
			for invoice in obj_invoice.search([('id','in',docids),('state','not in',['draft'])],order="name asc"):
				lines=[]
				vinvoice=self.get_line(invoice,date_format=date_format)
				if invoice.partner_id.id in partner_ids:
					data[partner_ids.index(invoice.partner_id.id)]['amount_total'] += vinvoice.get('amount_total',0)
					data[partner_ids.index(invoice.partner_id.id)]['amount_15'] += vinvoice.get('amount_15',0)
					data[partner_ids.index(invoice.partner_id.id)]['isv_15'] += vinvoice.get('isv_15',0)
					data[partner_ids.index(invoice.partner_id.id)]['amount_18'] += vinvoice.get('amount_18',0)
					data[partner_ids.index(invoice.partner_id.id)]['isv_18'] += vinvoice.get('isv_18',0)
					data[partner_ids.index(invoice.partner_id.id)]['amount_0'] += vinvoice.get('amount_0',0)
					if show_detail:
						data[partner_ids.index(invoice.partner_id.id)]['lines'].append(vinvoice)
				else:
					partner_ids.append(invoice.partner_id.id)
					val={
						'title_name':invoice.partner_id.name,
						'amount_total':vinvoice.get('amount_total',0),
						'amount_15':vinvoice.get('amount_15',0),
						'isv_15':vinvoice.get('isv_15',0),
						'amount_0':vinvoice.get('amount_0',0),
						'amount_18':vinvoice.get('amount_18',0),
						'isv_18':vinvoice.get('isv_18',0),
						'sub':True,
					}
					if show_detail:
						val.update({'lines':[vinvoice]})
					data.append(val)
				amount_total += vinvoice.get('amount_total',0)
				amount_15 += vinvoice.get('amount_15',0)
				isv_15 += vinvoice.get('isv_15',0)
				amount_0 += vinvoice.get('amount_0',0)
				amount_18 += vinvoice.get('amount_18',0)
				isv_18 += vinvoice.get('isv_18',0)

			valt = {
				'title_name':"TOTAL",
				'amount_total':amount_total,
				'amount_15':amount_15,
				'isv_15':isv_15,
				'amount_18':amount_18,
				'isv_18':isv_18,
				'amount_0':amount_0,
				'sub':True,
			}
			data.append(valt)
		elif group_by == 'month':
			amount_total = 0.0
			amount_15 = 0.0
			isv_15 = 0.0
			amount_18 = 0.0
			isv_18 = 0.0
			amount_0 = 0.0
			for invoice in obj_invoice.search([('id','in',docids),('state','not in',['draft'])],order="name asc"):
				vinvoice = self.get_line(invoice,date_format = date_format)
				if self.get_mes(invoice.invoice_date) in month_ids:
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['amount_total'] += vinvoice.get('amount_total',0)
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['amount_15'] += vinvoice.get('amount_15',0)
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['isv_15'] += vinvoice.get('isv_15',0)
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['amount_18'] += vinvoice.get('amount_18',0)
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['isv_18'] += vinvoice.get('isv_18',0)
					data[month_ids.index(self.get_mes(invoice.invoice_date))]['amount_0'] += vinvoice.get('amount_0',0)
					if show_detail:
						data[month_ids.index(self.get_mes(invoice.invoice_date))]['lines'].append(self.get_line(invoice,date_format=date_format))
				else:
					month_ids.append(self.get_mes(invoice.invoice_date))
					val = {
						'title_name': self.get_mes(invoice.invoice_date),
						'amount_total': vinvoice.get('amount_total',0),
						'amount_15': vinvoice.get('amount_15',0),
						'isv_15': vinvoice.get('isv_15',0),
						'amount_0': vinvoice.get('amount_0',0),
						'amount_18': vinvoice.get('amount_18',0),
						'isv_18': vinvoice.get('isv_18',0),
						'sub': True,
					}
					if show_detail:
						val.update({'lines':[self.get_line(invoice,date_format=date_format)]})
					data.append(val)
				amount_total += vinvoice.get('amount_total',0)
				amount_15 += vinvoice.get('amount_15',0)
				isv_15 += vinvoice.get('isv_15',0)
				amount_0 += vinvoice.get('amount_0',0)
				amount_18 += vinvoice.get('amount_18',0)
				isv_18 += vinvoice.get('isv_18',0)
			valt = {
				'title_name':"TOTAL",
				'amount_total':amount_total,
				'amount_15':amount_15,
				'isv_15':isv_15,
				'amount_18':amount_18,
				'isv_18':isv_18,
				'amount_0':amount_0,
				'sub':True,
			}
			data.append(valt)
		elif group_by == 'month_partner':
			amount_total=0.0
			amount_15=0.0
			isv_15=0.0
			amount_18=0.0
			isv_18=0.0
			amount_0=0.0
			for invoice in obj_invoice.search([('id','in',docids),('state','not in',['draft'])],order="name asc"):
				vinvoice=self.get_line(invoice,date_format=date_format)
				if self.get_mes(invoice.invoice_date) in month_ids:
					mid=month_ids.index(self.get_mes(invoice.invoice_date))
					data[mid]['amount_total']+=vinvoice.get('amount_total',0)
					data[mid]['amount_15']+=vinvoice.get('amount_15',0)
					data[mid]['isv_15']+=vinvoice.get('isv_15',0)
					data[mid]['amount_18']+=vinvoice.get('amount_18',0)
					data[mid]['isv_18']+=vinvoice.get('isv_18',0)
					data[mid]['amount_0']+=vinvoice.get('amount_0',0)
					if invoice.partner_id.id in data[mid]['partner_ids']:
						iposition=data[mid]['partner_ids'].index(invoice.partner_id.id)
						data[mid]['tlines'][iposition]['amount_total']+=vinvoice.get('amount_total',0)
						data[mid]['tlines'][iposition]['amount_15']+=vinvoice.get('amount_15',0)
						data[mid]['tlines'][iposition]['isv_15']+=vinvoice.get('isv_15',0)
						data[mid]['tlines'][iposition]['amount_18']+=vinvoice.get('amount_18',0)
						data[mid]['tlines'][iposition]['isv_18']+=vinvoice.get('isv_18',0)
						data[mid]['tlines'][iposition]['amount_0']+=vinvoice.get('amount_0',0)
						if show_detail:
							data[mid]['tlines'][data[mid]['partner_ids'].index(invoice.partner_id.id)]['lines'].append(self.get_line(invoice))
					else:
						data[mid]['partner_ids'].append(invoice.partner_id.id)
						val={
							'subtitle_name':invoice.partner_id.name,
							'amount_total':vinvoice.get('amount_total',0),
							'amount_15':vinvoice.get('amount_15',0),
							'isv_15':vinvoice.get('isv_15',0),
							'amount_0':vinvoice.get('amount_0',0),
							'amount_18':vinvoice.get('amount_18',0),
							'isv_18':vinvoice.get('isv_18',0),
							'sub':show_detail,
						}
						if show_detail:
							val.update({'lines':[self.get_line(invoice,date_format=date_format)]})
						data[mid]['tlines'].append(val)
				else:
					month_ids.append(self.get_mes(invoice.invoice_date))
					val1={
						'subtitle_name':invoice.partner_id.name,
						'amount_total':vinvoice.get('amount_total',0),
						'amount_15':vinvoice.get('amount_15',0),
						'isv_15':vinvoice.get('isv_15',0),
						'amount_0':vinvoice.get('amount_0',0),
						'amount_18':vinvoice.get('amount_18',0),
						'isv_18':vinvoice.get('isv_18',0),
						'sub':show_detail,
					}
					if show_detail:
						val1.update({'lines':[self.get_line(invoice,date_format=date_format)]})
					val={
						'title_name':self.get_mes(invoice.invoice_date),
						'amount_total':vinvoice.get('amount_total',0),
						'amount_15':vinvoice.get('amount_15',0),
						'isv_15':vinvoice.get('isv_15',0),
						'amount_0':vinvoice.get('amount_0',0),
						'amount_18':vinvoice.get('amount_18',0),
						'isv_18':vinvoice.get('isv_18',0),
						'sub':True,
						'tlines':[val1],
						'partner_ids':[invoice.partner_id.id],
						
					}
					
					data.append(val)
				amount_total+=vinvoice.get('amount_total',0)
				amount_15+=vinvoice.get('amount_15',0)
				isv_15+=vinvoice.get('isv_15',0)
				amount_0+=vinvoice.get('amount_0',0)
				amount_18+=vinvoice.get('amount_18',0)
				isv_18+=vinvoice.get('isv_18',0)
			valt={
			'title_name':"TOTAL",
			'amount_total':amount_total,
			'amount_15':amount_15,
			'isv_15':isv_15,
			'amount_18':amount_18,
			'isv_18':isv_18,
			'amount_0':amount_0,
			'sub':True,
			}
			data.append(valt)
		elif group_by == 'partner_month':
			amount_total=0.0
			amount_15=0.0
			isv_15=0.0
			amount_18=0.0
			isv_18=0.0
			amount_0=0.0
			for invoice in obj_invoice.search([('id','in',docids),('state','not in',['draft'])],order="name asc"):
				vinvoice=self.get_line(invoice,date_format=date_format)
				if invoice.partner_id.id in partner_ids:
					mid=partner_ids.index(invoice.partner_id.id)
					data[mid]['amount_total']+=vinvoice.get('amount_total',0)
					data[mid]['amount_15']+=vinvoice.get('amount_15',0)
					data[mid]['isv_15']+=vinvoice.get('isv_15',0)
					data[mid]['amount_18']+=vinvoice.get('amount_18',0)
					data[mid]['isv_18']+=vinvoice.get('isv_18',0)
					data[mid]['amount_0']+=vinvoice.get('amount_0',0)

					if self.get_mes(invoice.invoice_date) in data[mid]['month_ids']:
						iposition=data[mid]['month_ids'].index(self.get_mes(invoice.invoice_date))
						data[mid]['tlines'][iposition]['amount_total']+=vinvoice.get('amount_total',0)
						data[mid]['tlines'][iposition]['amount_15']+=vinvoice.get('amount_15',0)
						data[mid]['tlines'][iposition]['isv_15']+=vinvoice.get('isv_15',0)
						data[mid]['tlines'][iposition]['amount_18']+=vinvoice.get('amount_18',0)
						data[mid]['tlines'][iposition]['isv_18']+=vinvoice.get('isv_18',0)
						data[mid]['tlines'][iposition]['amount_0']+=vinvoice.get('amount_0',0)
						if show_detail:
							data[mid]['tlines'][data[mid]['month_ids'].index(self.get_mes(invoice.invoice_date))]['lines'].append(self.get_line(invoice,date_format=date_format))
					else:
						data[mid]['month_ids'].append(self.get_mes(invoice.invoice_date))
						val={
							'subtitle_name':self.get_mes(invoice.invoice_date),
							'amount_total':vinvoice.get('amount_total',0),
							'amount_15':vinvoice.get('amount_15',0),
							'isv_15':vinvoice.get('isv_15',0),
							'amount_0':vinvoice.get('amount_0',0),
							'amount_18':vinvoice.get('amount_18',0),
							'isv_18':vinvoice.get('isv_18',0),
							'sub':show_detail,
					
						}
						if show_detail:
							val.update({'lines':[self.get_line(invoice,date_format=date_format)]})
						data[mid]['tlines'].append(val)
				else:
					partner_ids.append(invoice.partner_id.id)
					val1={
						'subtitle_name':self.get_mes(invoice.invoice_date),
						'amount_total':vinvoice.get('amount_total',0),
						'amount_15':vinvoice.get('amount_15',0),
						'isv_15':vinvoice.get('isv_15',0),
						'amount_0':vinvoice.get('amount_0',0),
						'amount_18':vinvoice.get('amount_18',0),
						'isv_18':vinvoice.get('isv_18',0),
						'sub':show_detail,
					}
					if show_detail:
						val1.update({'lines':[self.get_line(invoice,date_format=date_format)]})
					val={
						'title_name':invoice.partner_id.name,
						'amount_total':vinvoice.get('amount_total',0),
						'amount_15':vinvoice.get('amount_15',0),
						'isv_15':vinvoice.get('isv_15',0),
						'amount_0':vinvoice.get('amount_0',0),
						'amount_18':vinvoice.get('amount_18',0),
						'isv_18':vinvoice.get('isv_18',0),
						'sub':True,
						'tlines':[val1],
						'month_ids':[self.get_mes(invoice.invoice_date)],
						
					}
					
					data.append(val)
				amount_total+=vinvoice.get('amount_total',0)
				amount_15+=vinvoice.get('amount_15',0)
				isv_15+=vinvoice.get('isv_15',0)
				amount_0+=vinvoice.get('amount_0',0)
				amount_18+=vinvoice.get('amount_18',0)
				isv_18+=vinvoice.get('isv_18',0)
			valt={
			'title_name':"TOTAL",
			'amount_total':amount_total,
			'amount_15':amount_15,
			'isv_15':isv_15,
			'amount_18':amount_18,
			'isv_18':isv_18,
			'amount_0':amount_0,
			'sub':True,
			}
			data.append(valt)
		else:
			amount_total=0.0
			amount_15=0.0
			isv_15=0.0
			amount_18=0.0
			isv_18=0.0
			amount_0=0.0
			for invoice in obj_invoice.search([('id','in',docids),('state','not in',['draft'])],order="name asc"):
				vinvoice = self.get_line(invoice,date_format=date_format)
				amount_total += vinvoice.get('amount_total',0)
				amount_15 += vinvoice.get('amount_15',0)
				isv_15 += vinvoice.get('isv_15',0)
				amount_0 += vinvoice.get('amount_0',0)
				amount_18 += vinvoice.get('amount_18',0)
				isv_18 += vinvoice.get('isv_18',0)
				if show_detail:
					data.append(vinvoice)
			valt={
			'title_name':"TOTAL",
			'amount_total':amount_total,
			'amount_15':amount_15,
			'isv_15':isv_15,
			'amount_18':amount_18,
			'isv_18':isv_18,
			'amount_0':amount_0,
			'sub':True,
			}
			data.append(valt)
		return data
