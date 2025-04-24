# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
import re
import time
from datetime import date, timedelta,datetime
import logging
from copy import copy
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class SaleConfigSettings(models.TransientModel):
	_name = 'cm.web.sale_order'
	_description = "Ordenes de venta Web"
	_inherit = ['res.config.settings','mail.thread', 'mail.activity.mixin']

	pnr 				= fields.Char(string="PNR Code")
	pnr_ids 			= fields.Char(string="PNRs")
	salestatement_ids	= fields.Many2many('sale.statement_odoo',string="Sale Statements")
	cashstatement_ids	= fields.Many2many('sale.cashstatement_odoo',string="Cash Statements")
	date_start			= fields.Date("Date Start")
	date_end			= fields.Date("Date Stop")

	def final_lines(self,lines,company_id):
		res=[]
		YQAmount=0.0
		TAAmount=0.0
		YRAmount=0.0
		FHAmount=0.0
		HNAmount=0.0
		YZAmount=0.0
		TDAmount=0.0
		TIAmount=0.0


		tax_ids=[]
		company=self.env.user.company_id
		for linet in lines:
			line=linet[2]
			if line.get('price_unit')>=0:
				YQAmount+=line.get('YQAmount',0.0)
				TAAmount+=line.get('TAAmount',0.0)
				YRAmount+=line.get('YRAmount',0.0)
				YZAmount+=line.get('YZAmount',0.0)
				TDAmount+=line.get('TDAmount',0.0)
				TIAmount+=line.get('TIAmount',0.0)
			if line.get('price_unit')<0:
				YQAmount-=line.get('YQAmount',0.0)
				TAAmount-=line.get('TAAmount',0.0)
				YRAmount-=line.get('YRAmount',0.0)
				YZAmount-=line.get('YZAmount',0.0)
				TDAmount-=line.get('TDAmount',0.0)
				TIAmount-=line.get('TIAmount',0.0)
			t=line.get('invoice_line_tax_ids',[(6,0,[])])
			if len(t[0][2])>0 and line.get('YQAmount',0.0)>0:
				tax_ids=t
		if company_id:
			company=self.env.get('res.company').browse(company_id)
		line={
			'name':'YQ AMOUNT',
			'account_id':company.yq_account_id.id,
			'quantity':1,
			'price_unit':YQAmount,
			'invoice_line_tax_ids':tax_ids,
			'sub_invoice':False,
		}
		if YQAmount!=0:
			res.append((0,0,line))
		line={
			'name':'YR AMOUNT',
			'account_id':company.yr_account_id.id,
			'quantity':1,
			'price_unit':YRAmount,
			'sub_invoice':False,
			'invoice_line_tax_ids':tax_ids,
		}
		if YRAmount!=0:
			res.append((0,0,line))
		line={
			'name':'TA AMOUNT',
			'account_id':company.ta_account_id.id,
			'quantity':1,
			'price_unit':TAAmount,
			'sub_invoice':False,
		}
		if TAAmount!=0:
			res.append((0,0,line))
		line={
			'name':'YZ AMOUNT',
			'account_id':company.yz_account_id.id,
			'quantity':1,
			'price_unit':YZAmount,
			'sub_invoice':False,
			'invoice_line_tax_ids':tax_ids,
		}
		if YZAmount!=0:
			res.append((0,0,line))
		line={
			'name':'TD AMOUNT',
			'account_id':company.td_account_id.id,
			'quantity':1,
			'price_unit':TDAmount,
			'sub_invoice':False,
			'account_analytic_id':company.td_analytic_id.id,
		}
		if TDAmount!=0:
			res.append((0,0,line))
		line={
			'name':'TI AMOUNT',
			'account_id':company.ti_account_id.id,
			'quantity':1,
			'price_unit':TIAmount,
			'sub_invoice':False,
			'account_analytic_id':company.ti_analytic_id.id,
		}
		if TIAmount!=0:
			res.append((0,0,line))
		return res
	def lines_invoice(self,stament,position):
		if stament.state=='done':
			return 
		company_id=stament.partner_id.company_id.id or stament.PointOfSaleID.company_id.id 
		if str(stament.PaymentMode.replace(' ', '')) =="Contado":
			company_id=stament.PointOfSaleID.company_id 
		else:
			company_id=stament.partner_id.company_id
		if stament.company_id:
			company_id=stament.company_id
		account_id=None
		for line in  stament.StatementTypeID.transaction_ids:
			if company_id.id==line.company_id.id:
				account_id=line.account_id.id		
		if not company_id.id or not account_id or not stament.currency_id:
			stament.error=True
			return 
		journal_id=company_id.journal_account_id.id 
		if stament.PointOfSaleID.journal_id:
			journal_id=stament.PointOfSaleID.journal_id.id
		tax_ids=[]
		external_tax=0
		YQAmount=stament.YQAmount
		YZAmount=stament.YZAmount
		YRAmount=stament.YRAmount
		addisv=False
		if  stament.StatementTypeID.dcalculate == 'always':
			addisv=True
		elif stament.StatementTypeID.dcalculate == 'based' and position:
			addisv=True
		if stament.HNAmount+stament.FHAmount !=0  and stament.BaseCurrencyAmount!=0:
			addisv=False
			tax_ids2=self.env.get('account.tax').search([('consumer','=',True),('company_id','=',company_id.id)])
			tax_ids=tax_ids2.ids
			for tax in tax_ids2:
				temp=YQAmount/(1+(tax.amount/100.0))
				external_tax+=YQAmount-temp
				YQAmount=temp
				temp=YZAmount/(1+(tax.amount/100.0))
				external_tax+=YZAmount-temp
				YZAmount=temp
				temp=YRAmount/(1+(tax.amount/100.0))
				external_tax+=YRAmount-temp
				YRAmount=temp
		price_unit=0
		vem=0
		dem=1
		if str(stament.PassengerType).replace(' ', '') =='SRC':
			dem=0.75
			vem=25
		price_unit=(stament.BaseCurrencyAmount-stament.BaseCurrencyTaxAmount)/dem
		tasa=stament.TDAmount+stament.TIAmount
		if price_unit==0 and (stament.BaseCurrencyAmount==0 or tasa==0):
			stament.state='done'
			return 
		
		if addisv:
			tax_ids2=self.env.get('account.tax').search([('consumer','=',True),('company_id','=',company_id.id)])
			tax_ids=tax_ids2.ids
			for tax in tax_ids2:
				temp=round(price_unit/(1+(tax.amount/100)),3)
				price_unit=temp
	
		if stament.BaseCurrencyAmount==0:
			YQAmount=0
			YZAmount=0
			YRAmount=0
		label=stament.RecordStatement
		donate=stament.StatementTypeID.donate
		if stament.StatementTypeID.ulabel:
			label=stament.StatementTypeID.label
		TAAmount=stament.TAAmount
		TDAmount=stament.TDAmount
		TIAmount=stament.TIAmount
		
		#YRAmount=stament.YRAmount
		if not stament.StatementTypeID.external_tax:
			TAAmount=0
			YRAmount=0
			YQAmount=0
			YZAmount=0
		term_text='account.account_payment_term_15days'
		if str(stament.PaymentMode).replace(' ', '') =="Contado":
			term_text='account.account_payment_term_immediate'
		cont_term=self.env.ref(term_text)
		#stament.AgentID.user_id.company_id=:company_id.id
		pk2_id="%s-%s"%(str(stament.PNRCode),str(stament.AgentID2))
		pk2_id=stament.PNRCode
		vals={
			'payment_term_id':cont_term.id,
			'discount':vem,
			'pk2_id':pk2_id,
			'currency_id':stament.currency_id.id,
			'stament_id':stament,
			'name':label,
			'account_id':account_id,
			'quantity':1,
			'price_unit':price_unit,
			'invoice_line_tax_ids':[(6,0,tax_ids)],
			'external_tax':external_tax,
			'partner_id':stament.partner_id,
			'PNRCODE':stament.PNRCode,
			'PointOfSaleID':stament.PointOfSaleID.name,
			'company_id':company_id.id,
			
			'AgentID2':stament.AgentID2,
			'user_id':stament.AgentID.user_id.id,
			'TAAmount':TAAmount,
			'YRAmount':YRAmount,
			'YQAmount':YQAmount,
			'TDAmount':TDAmount,
			'TIAmount':TIAmount,
			'YZAmount':YZAmount,
			'journal_id':journal_id,
			'state':stament.state,
			'rtn_name':stament.rtn,
			'partner_name':stament.name,
			'invoice_date':stament.SaleStatementDateAndHourLT,
			'donate':donate,
			
		}
		return vals
	def consolidate_cash(self,cash):
		journal_ids=[]
		res=[]
		for line in cash:
			if line.get('pk_id') in journal_ids:
				p=journal_ids.index(line.get('pk_id'))
				res[p].update({'amount':line.get('amount')+res[p].get('amount'),'cash_id':res[p].get('cash_id')+line.get('cash_id')})
			else:
				journal_ids.append(line.get('pk_id'))
				#line.update({'cash_id':[]})
				res.append(line)
		return res
	def lines_cash(self,cash):
		if cash.state=='done':
			return
		company_id= cash.PointOfSaleID.company_id.id
		if cash.company_id:
			company_id= cash.company_id.id
		if not company_id:
			return
		nro_auto=""
		card_digits=""
		text=cash.RecordReferenceNumber or ""
		text=re.sub('[^A-Za-z0-9--]+', '', text)
		texts=text.split("-")
		if len(texts)>1:
			card_digits=texts[0]
			nro_auto=texts[1]
		pk_id=str(cash.FormOfPaymentID.id)+str(nro_auto)+str(card_digits)
		pk2_id="%s-%s"%(str(cash.PNRCode),str(cash.AgentID2))
		pk2_id=cash.PNRCode
		vals={
			'payment_date':cash.CashStatementDateAndHourLT,
			'pk_id':pk_id,
			'pk2_id':pk2_id,
			'state':cash.state,
			'is_sync':True,
			'currency_id':cash.currency_id.id,
			'cash_id':[cash],
			'obs':cash.RecordStatement,
			'journal_id':cash.FormOfPaymentID.id,
			'BaseCurrency':cash.BaseCurrency,
			'amount':cash.residual,
			'communication':cash.PNRCode,
			'PointOfSaleID':cash.PointOfSaleID.id,
			'company_id':company_id,
			'AgentID':cash.AgentID,
			'AgentID2':cash.AgentID2,
			'user_id':cash.AgentID.user_id.id,
			'partner_id':cash.partner_id.id,
			'partner_type':'customer',
			'payment_type':'inbound',
			'nro_auto':nro_auto,
			'card_digits':card_digits,
			'payment_method_id':self.env.ref('account_check_printing.account_payment_method_check').id
		}
		return vals

	def invoice(self):
		depfilters=[]
		depfilterscash=[]
		obj_invoice=self.env.get('account.invoice')
		obj_payment=self.env.get('account.payment')
		indexD=[]
		indexp=[]
		pindexp=[]
		position=False
		salestatement_ids=[]
		#CashStatementID
		#SaleStatementID
		for stament in self.salestatement_ids.sorted(key=lambda r: r.BaseCurrencyAmount,reverse=True):
			if stament.SaleStatementID in salestatement_ids:
				stament.error=True
				stament.invoice=False
			else:
				salestatement_ids.append(stament.SaleStatementID)
				pk_id="%s-%s"%(str(stament.PNRCode),str(stament.AgentID2))
				pk_id=stament.PNRCode
				print (pk_id,"#"*50)
				if pk_id not in indexp:
					indexp.append(pk_id)
					pindexp.append(False)
				p=indexp.index(pk_id)
				if stament.HNAmount+stament.FHAmount>0:
					pindexp[p]=True
				if stament.state=='draft' and stament.invoice:
					indexD.append(pk_id)
					new_line=self.lines_invoice(stament,pindexp[p])
					if new_line:
						depfilters.append(new_line)
		cashstatement_ids=[]	
		for cash in self.cashstatement_ids:
			if cash.CashStatementID in cashstatement_ids:
				cash.error=True
				cash.invoice=False
			else:
				cashstatement_ids.append(cash.CashStatementID)
			if cash.state=='draft' and cash.invoice:
				pk_id="%s-%s"%(str(cash.PNRCode),str(cash.AgentID2))
				pk_id=cash.PNRCode
				indexD.append(pk_id)
				cnew_line=self.lines_cash(cash)
				if cnew_line:
					depfilterscash.append(cnew_line)
		flista=list(set(indexD))
		for data in flista:
			pdta=data
			ddpnr=data.split("-")
			if len(ddpnr)>0:
				pdta=ddpnr[0]
			_logger.info('Create a PNR %s', data)
			lines=[]
			partner_id=None

			user_id=None
			currency_id=None
			company_id=None
			journal_id=None
			rtn_name=None
			partner_name=None
			statment_ids=[]
			PointOfSaleID=None
			invoice_date=False
			#arrayp=filter(lambda line: "%s-%s"%(str(line.get('PNRCODE')),str(line.get('AgentID2'))) == data,copy(depfilters) )
			arrayp=filter(lambda line: line.get('PNRCODE') == data,copy(depfilters) )
			print ("%")
			print (arrayp)
			for line in arrayp:
				if not company_id:
					company_id=line.get('company_id')
					
				else:
					if company_id!=line.get('company_id'):
						continue
				del(line['company_id'])
				statment_ids.append(line.get('stament_id'))
				user_id=line.get('user_id',self.env.user.id)
				partner_id=line.get('partner_id')
				currency_id=line.get('currency_id')
				payment_term_id=line.get('payment_term_id')
				
				journal_id=line.get('journal_id')
				if line.get('partner_name'):
					partner_name=line.get('partner_name')
				if line.get('rtn_name'):
					rtn_name=line.get('rtn_name')
				PointOfSaleID=line.get('PointOfSaleID') or PointOfSaleID
				invoice_date=line.get('invoice_date')
				del(line['invoice_date'])
				del(line['stament_id'])
				del(line['user_id'])
				del(line['currency_id'])
				
				del(line['partner_id'])
				del(line['journal_id'])
				del(line['PointOfSaleID'])
				del(line['partner_name'])
				del(line['rtn_name'])
				lines.append((0,0,line))
			lines+=self.final_lines(lines,company_id)
			vals={}
			if self.env.user.id!=1 and company_id:
				self.env.user.company_id=company_id
			if partner_id:
				company_cxt = dict(self.env.context, force_company=company_id)
				account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id', 'res.partner')
				account_id =  (account_def and account_def.id) or (partner_id.property_account_receivable_id.id) or False
				vals={
					'partner_name':partner_name,
					'rtn_name':rtn_name,
					'pk2_id':data,
					'user_id':user_id,
					'company_id':company_id,
					'partner_id':partner_id.id,
					'journal_id':journal_id,
					'invoice_line_ids':lines,
					'name':pdta,
					'currency_id':currency_id,
					'is_sync':True,
					'type': 'out_invoice',
					'reference': PointOfSaleID,
					'date_invoice':invoice_date,
					'payment_term_id':payment_term_id or partner_id.property_payment_term_id.id,
					#'account_id': partner_id.property_account_receivable_id.id,
				}
				if account_id:
					vals.update({'account_id':account_id})
			res_id=None
			old_company=self.env.user.company_id.id
			if len(vals.get('invoice_line_ids',[]))>0 and journal_id and company_id and vals:
				try:
					res_id=obj_invoice.create(vals)
				except:
					for statment_id in statment_ids:
						statment_id.error=True
				
				if res_id:
					for statment_id in statment_ids:
						statment_id.state="done"
			else:
				for statment_id in statment_ids:
					statment_id.error=True
			inv_ids=[]
			domain=[('pk2_id','=',data),('state','in',['draft','done','open'])]
			inv_ids=obj_invoice.search(domain,order='id desc')
			if len(inv_ids)==0:
				continue
			newarray=copy(depfilterscash)
			arrayc1=filter(lambda line: line.get('pk2_id') == data, depfilterscash)
			arrayc=self.consolidate_cash(arrayc1)
			for res_id in inv_ids:
				try:
					res_id.action_invoice_open()
				except:
					continue
				ctx={'default_invoice_ids': [(4, res_id.id, None)]}
				for linecash in arrayc:
					residual=res_id.residual
					if linecash.get('journal_id') and linecash.get('amount')>0 and linecash.get('company_id')==res_id.company_id.id and residual>0:
						diff=linecash.get('amount')-residual
						cdiff=0
						if diff>1:
							linecash.update({'amount':residual})
							for cash_id in linecash.get('cash_id'):
								if residual <= 0:
									continue
								cdiff=cash_id.residual-residual
								residual+=-cash_id.residual
								if cdiff>0:
									cash_id.residual=cdiff
								else:
									cash_id.state="done"
									cash_id.residual=0
						elif diff<-1:
							for cash_id in linecash.get('cash_id'):
								cash_id.state="done"
								cash_id.residual=0
						else:
							linecash.update({'amount':residual})
							for cash_id in linecash.get('cash_id'):
								cash_id.state="done"
								cash_id.residual=0
						try:
							pres_id=obj_payment.with_context(ctx).create(linecash)
							pres_id.post()
							linecash.update({'amount':cdiff})
						except:
							for cash_id in linecash.get('cash_id'):
								_logger.info('Error in cash %s', str(cash_id.id))
								cash_id.error=True
					elif linecash.get('journal_id') and len(linecash.get('cash_id'))>1:
						for cash_id in linecash.get('cash_id'):
							cash_id.state="done"
					else:
						for cash_id in linecash.get('cash_id'):
							cash_id.error=True
			self.env.user.company_id=old_company
		return self.action_view_invoice()
		
	def action_view_invoice(self):
		self.ensure_one()
		invoices=[]
		action = self.env.ref('cm_sales.action_invoice_view').read()[0]
		for line in self.salestatement_ids:
			invoices.append(line.PNRCode)
		invoice_ids=self.env.get('account.invoice').search([('name', 'in', invoices)]).ids
		if len(invoice_ids) > 1:
			action['domain'] = [('id', 'in', invoice_ids)]
		elif len(invoice_ids) == 1:
			action['views'] = [(self.env.ref('cm_sales.invoice_form_view').id, 'form')]
			action['res_id'] = invoice_ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action

	def cancel_order(self):
		self.salestatement_ids=None
		self.cashstatement_ids=None
		self.pnr=None

	@api.model
	def post_order(self):
		a=self.create({})
		a.with_context({'total':True}).post_ws()

	@api.model
	def validate_order(self,limit_no=False):
		limit=self.env.context.get("limit_no",False)
		obj_stament=self.env.get('sale.statement_odoo')
		obj_cash=self.env.get('sale.cashstatement_odoo')
		domain=[('state','=','draft'),('error','=',False)]
		domain2=[('state','=','draft'),('error','=',False),('PNRCode','!=',False),('invoice','=',True)]
		salestatement_ids=obj_stament.search(domain2,order="SaleStatementDateAndHourLT asc",limit=limit_no).ids
		_logger.info("No %i"%len(salestatement_ids))
		cashstatement_ids=obj_cash.search(domain).ids
		a=self.create({'salestatement_ids':[(6,0,salestatement_ids)],'cashstatement_ids':[(6,0,cashstatement_ids)]})
		a.invoice()
	def validate_order2(self,limit_no=300):
		limit=self.env.context.get("limit_no",False)
		obj_stament=self.env.get('sale.statement_odoo')
		obj_cash=self.env.get('sale.cashstatement_odoo')
		domain=[('state','=','draft'),('error','=',False)]
		domain2=[('state','=','draft'),('error','=',False),('invoice','=',True),('PNRCode','!=',False)]
		salestatement_ids=obj_stament.search(domain2,order="SaleStatementDateAndHourLT asc",limit=limit_no).ids
		_logger.info("No %i"%len(salestatement_ids))
		cashstatement_ids=obj_cash.search(domain).ids
		a=self.create({'salestatement_ids':[(6,0,salestatement_ids)],'cashstatement_ids':[(6,0,cashstatement_ids)]})
		a.invoice()

	def reinvoice(self):
		company_id=self.env.user.company_id.id
		journal_obj=self.env.get('account.journal')
		obj_invoice=self.env.get('account.invoice')
		for sale in self.salestatement_ids:
			if sale.invoice:
				sale.company_id=company_id
				PNRCode=sale.PNRCode
				domain=[('name','=',PNRCode),('state','in',['open','paid','done'])]
				#inv_ids=obj_invoice.search(domain,order='id desc')
				#if len(inv_ids)>0:
				#	text=', '.join(map(lambda x: x.number ,inv_ids))
				#	raise UserError("Primero Cancele las Facturas "+text+" con el PNRCODE "+PNRCode)
				sale.state='draft'
		for cash in self.cashstatement_ids:
			if cash.invoice:
				journal_ids=journal_obj.search([('company_id','=',company_id),('equivalence','=',cash.FormOfPaymentID2)]).ids
				journal_id=None
				cash.state='draft'
				if len(journal_ids)>0:
					journal_id=journal_ids[0]
				cash.FormOfPaymentID=journal_id
				cash.company_id=company_id
				cash.residual=cash.BaseCurrencyAmount
		return self.invoice()
		
	def charge_local(self):
		self.ensure_one()
		if self.pnr_ids:
			PNR_CODES=self.pnr_ids.split(",")
			self.salestatement_ids=None
			self.cashstatement_ids=None
			domain=[('PNRCode','in',PNR_CODES)]
			self.salestatement_ids=[(6,0,self.salestatement_ids.search(domain).ids)]
			self.cashstatement_ids=[(6,0,self.cashstatement_ids.search(domain).ids)]
			
	def cancel_invoice(self):
		self.ensure_one()
		if self.pnr_ids:
			PNR_CODES=self.pnr_ids.split(",")
			domain=[('name','in',PNR_CODES)]
			print (domain)
			if self.date_start:
				domain.append(('date_invoice','>=',self.date_start))
			if self.date_end:
				domain.append(('date_invoice','<=',self.date_end))
			invoice_ids=self.env.get("account.invoice").search(domain)
			#if self.date_start:
				#domain.append(('date_invoice','>=',self.date_start))
			#if self.date_end:
				#domain.append(('date_invoice','<=',self.date_end))
			#invoice_ids=self.env.get("account.invoice").search(domain)
			for invoice in invoice_ids:
				print (invoice.state)
				print (invoice.name)
				for payment in invoice.payment_ids:
					payment.cancel()
				if invoice.state!='cancel':
					invoice.action_invoice_cancel()

	def post_ws(self):
		#body ="Se Presionó el boton de Verificar con Fecha de Inicio: %s y Fecha Final: %s" % (self.date_start,self.date_end)
		#self.message_post(body=body)
		force_company=None
		self.salestatement_ids=None
		self.cashstatement_ids=None
		self.ensure_one()
		dpnr=False
		ddate_start=False
		ddate_stop=False
		if self.pnr:
			dpnr=self.pnr
		elif self.date_start and self.date_end:
			ddate_start=self.date_start
			ddate_stop=self.date_end
		elif self.env.context.get('today',False):
			ddate_start=fields.Date.context_today(self)
			ddate_stop= (datetime.strptime(fields.Date.context_today(self), '%Y-%m-%d').date()+timedelta(days=1)).strftime('%Y-%m-%d')
		elif not self.env.context.get('total',False):
    		
			return
		if not dpnr and not ddate_start and not ddate_stop:
			ddate_start=fields.Date.context_today(self)
			ddate_stop= (datetime.strptime(fields.Date.context_today(self), '%Y-%m-%d').date()+timedelta(days=1)).strftime('%Y-%m-%d')
		_logger.info("DATE START STOP")
		_logger.info(self.env.context.get('today',False))
		_logger.info(ddate_start)
		_logger.info(ddate_stop)
		_logger.info("PNR")
		_logger.info(dpnr)
		#_logger.info(ddate_stop)
		
		host_met=self.env.user.company_id.from_host_id
		vals=host_met.GetStatementsODOO(dpnr,ddate_start,ddate_stop)
		sale_ids=[]
		cash_ids=[]
		sale_obj=self.env.get('sale.statement_odoo')
		cash_obj=self.env.get('sale.cashstatement_odoo')
		pos_obj=self.env.get('sale.point_of_sale')
		agent_obj=self.env.get('sale.agent')
		partner_obj=self.env.get('res.partner')
		currency_obj=self.env.get('res.currency')
		transaction_obj=self.env.get('sale.transaction')
		journal_obj=self.env.get('account.journal')
		for sale in vals.get('SaleStatements',[]):
			if not sale.get('PNRCode'):
				continue
			sale.update({'StatementTypeID2':sale.get('StatementTypeID')})
			dsale=sale_obj.search([('SaleStatementID','=',sale.get('SaleStatementID'))]).ids
			
			vdsale_ids=transaction_obj.search([('equivalence','=',sale.get('StatementTypeID'))])
			trs_ids=vdsale_ids.ids
			find_value=False
			for vd in vdsale_ids:
				find_value=vd.find_value
			if find_value:
				cadena=sale.get('RecordStatement','').lower()
				#_logger.info(cadena)
				newcadena=cadena.split()
				if 'lb' in newcadena:
					indexcadena=newcadena.index('lb')
					valuecadena=newcadena[indexcadena-1]
					valuecadena=valuecadena.replace(',',".")
					fvalue=0.0
					try:
						fvalue=float(valuecadena)
					except:
						fvalue=0.0
					
					bvalue=float(sale.get('BaseCurrencyAmount',0))
					dfvalue=fvalue-bvalue
					is_diff=False
					if dfvalue!=0:
						is_diff=True
					sale.update({'value':bvalue,'find_value':True,'diff_value':dfvalue,'is_diff':is_diff})
			trs_id=None
			if len(trs_ids)>0:
				trs_id=trs_ids[0]
			
			sale.update({'StatementTypeID':trs_id})
			pos_ids=pos_obj.search([('equivalence','=',sale.get('PointOfSaleID'))])
			company_id=None
			partner_ids=partner_obj.search([('equivalence','=',sale.get('CustomerID'))])
			partner_id=None
			if len(partner_ids)>0:
				partner_id=partner_ids[0]
			else:
				partner_ids=partner_obj.search([('consumer','=',True)])
				if len(partner_ids)>0:
					partner_id=partner_ids[0]
			sale.update({'partner_id':partner_id.id})
			
			pos_id=None
			if str(sale.get('PaymentMode',"")).replace(' ', '') =="Contado":
				if len(pos_ids)>0:
					company_id=pos_ids[0].company_id.id
					pos_id=pos_ids[0].id
			else:
				company_id=partner_id.company_id.id
			if force_company:
				company_id=company_id
			sale.update({'company_id':company_id})
			sale.update({'PointOfSaleID2':sale.get('PointOfSaleID')})
			sale.update({'PointOfSaleID':pos_id})
			agent_ids=agent_obj.search([('equivalence','=',sale.get('AgentID'))])
			agent_id=None
			condition=True
			if self.env.context.get('today',False):
				condition=True
			if len(agent_ids)>0:
				agent_id=agent_ids[0].id
				#if self.env.context.get('today',False):
				#	condition=agent_ids[0].user_id.id==self.env.user.id
			sale.update({'AgentID2':sale.get('AgentID')})
			sale.update({'AgentID':agent_id})
			#currency_ids=currency_obj.search([('name','=',sale.get('SaleCurrency'))]).ids
			currency_ids=currency_obj.search([('name','=','USD')]).ids
			currency_id=None
			if len(currency_ids)>0:
				currency_id=currency_ids[0]
			sale.update({'currency_id':currency_id})

			
			if len(dsale)==0 and condition:
				sale_ids.append((0,0,sale))
			elif len(dsale)==1 and condition:
				self.update_sale(sale,dsale[0])
				sale_ids.append((4,dsale[0]))

			elif condition:
				sale_ids.append((6,0,dsale))
		for cash in vals.get('CashStatements',[]):
			if not cash.get('PNRCode'):
				continue
			dcash=cash_obj.search([('CashStatementID','=',cash.get('CashStatementID'))]).ids
			pos_ids=pos_obj.search([('equivalence','=',cash.get('PointOfSaleID'))])
			company_id=None
			pos_id=None
			
			
			partner_ids=partner_obj.search([('equivalence','=',cash.get('CustomerID'))])
			partner_id=None
			if len(partner_ids)>0:
				partner_id=partner_ids[0]
			else:
				partner_ids=partner_obj.search([('consumer','=',True)])
				if len(partner_ids)>0:
					partner_id=partner_ids[0]
			cash.update({'partner_id':partner_id.id})
			if len(pos_ids)>0:
				company_id=pos_ids[0].company_id.id
				pos_id=pos_ids[0].id
			if not company_id :
				company_id=partner_id.company_id.id
			if force_company:
				company_id=company_id
			cash.update({'PointOfSaleID2':cash.get('PointOfSaleID')})
			cash.update({'PointOfSaleID':pos_id})
			cash.update({'company_id':company_id})
			#currency_ids=currency_obj.search([('name','=',cash.get('BaseCurrency'))]).ids
			currency_ids=currency_obj.search([('name','=','USD')]).ids
			currency_id=None
			if len(currency_ids)>0:
				currency_id=currency_ids[0]
			cash.update({'currency_id':currency_id})
			
			agent_ids=agent_obj.search([('equivalence','=',cash.get('AgentID'))])
			agent_id=None
			condition=True
			if self.env.context.get('today',False):
				condition=True
			if len(agent_ids)>0:
				agent_id=agent_ids[0].id
				#if self.env.context.get('today',False):
				#	condition=agent_ids[0].user_id.id==self.env.user.id
			cash.update({'AgentID2':cash.get('AgentID')})
			cash.update({'AgentID':agent_id})
			journal_ids=journal_obj.search([('company_id','=',company_id),('equivalence','=',int(float(cash.get('FormOfPaymentID'))))]).ids
			journal_id=None
			if len(journal_ids)>0:
				journal_id=journal_ids[0]
			cash.update({'FormOfPaymentID2':cash.get('FormOfPaymentID')})
			cash.update({'FormOfPaymentID':journal_id})
			cash.update({'residual':cash.get('BaseCurrencyAmount')})
			if len(dcash)==0 and condition:
				cash_ids.append((0,0,cash))
			elif len(dcash)==1  and condition:
				self.update_cash(cash,dcash[0])
				cash_ids.append((4,dcash[0]))
			elif condition:
				cash_ids.append((6,0,dcash))
				
		#self.env['sale.statement_odoo'].create({
		#	'RecordStatement': 'Se ejecuto post_ws',
		#	'SaleStatementDateAndHourLT': ddate_start
		#})

		self.salestatement_ids=sale_ids
		self.cashstatement_ids=cash_ids
		self.pnr=None
		self.date_start =None
		self.date_end =None
	def update_cash(self,cash,id):
		cash_obj=self.env.get('sale.cashstatement_odoo')
		cash_id= cash_obj.browse(id)
		if cash_id.state=='draft':
			val={
				'AgentID':cash.get('AgentID'),
				'PointOfSaleID':cash.get('PointOfSaleID'),
				'FormOfPaymentID':cash.get('FormOfPaymentID'),
				'partner_id':cash.get('partner_id'),
			}
			cash_id.write(val)

	def update_sale(self,sale,id):
		sale_obj=self.env.get('sale.statement_odoo')
		sale_id=sale_obj.browse(id)
		if sale_id.state=='draft':
			val={
				'AgentID':sale.get('AgentID'),
				'PointOfSaleID':sale.get('PointOfSaleID'),
				'StatementTypeID':sale.get('StatementTypeID'),
				'StatementTypeID2':sale.get('StatementTypeID2'),
				'partner_id':sale.get('partner_id'),
			}
			sale_id.write(val)
