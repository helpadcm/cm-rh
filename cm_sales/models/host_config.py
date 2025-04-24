# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from suds.client import Client
import suds

class res_company(models.Model):
	_inherit = 'res.company'
	
	from_host_id 			= fields.Many2one('sync.host',string='From')
	journal_account_id		= fields.Many2one('account.journal',string="Journal invoice")
	ta_account_id			= fields.Many2one('account.account',string="TA account")
	yr_account_id			= fields.Many2one('account.account',string="YR account")
	yq_account_id			= fields.Many2one('account.account',string="YQ account")
	yz_account_id			= fields.Many2one('account.account',string="YZ account")
	td_account_id			= fields.Many2one('account.account',string="TD account")
	ti_account_id			= fields.Many2one('account.account',string="TI account")
	ti_analytic_id			= fields.Many2one('account.analytic.account',string="TI analytic account")
	td_analytic_id			= fields.Many2one('account.analytic.account',string="TD analytic account")

class host_config(models.Model):
	_name = 'sync.host'
	_description = "Hosting de sincronizacion"
	_rec_name='wsdl'

	wsdl = fields.Char(string="Wsdl")
	login = fields.Char(string="Login")
	password = fields.Char(string="Password")
	airlinevendorid = fields.Char(string="AirlineVendorID")
	url="http://preprod4.ttinteractive.com/TTIDotNet/WebService/Internal/RevenueAccountingWebService/RevenueAccountingService.svc?wsdl"

	def test(self):
		a=""
		client = self.conect()
		for service in client.wsdl.services:
			for port in service.ports:
				methods = port.methods.values()
				for method in methods:
					a+= method.name+" "+port.name+"\n"
		raise UserError('Ok\n the methods are \n'+a)
				
	def GetStatementsODOO(self,PNRCode,StartDateLT,EndDateLT):
		try:
			x=self.GetStatementsODOO_detail(PNRCode,StartDateLT,EndDateLT)
		except:
			return self.GetStatementsODOO(PNRCode,StartDateLT,EndDateLT)
		res= self.parser_web(x)
		return res
		
	#@timeout(5)		
	def GetStatementsODOO_detail(self,PNRCode,StartDateLT,EndDateLT):
		client=self.conect()
		if not client:
			raise UserError("Bad Configuration")
		pos_object = client.factory.create('Source')
		tet=client.factory.create('GetStatementsODOO')
		tet.request.UseWrappedExceptionInFaultException=False
		tet.request.Login = self.login
		#001FY8
		if PNRCode:
			tet.request.PNRCode = PNRCode
		elif StartDateLT and EndDateLT:
    			
			tet.request.StartDateLT=StartDateLT
			tet.request.EndDateLT=EndDateLT
		tet.request.Password = self.password
		pos_object._AirlineVendorID = self.airlinevendorid
		tet.request.POS.Source.append(pos_object)
		a= client.service.GetStatementsODOO(tet.request)
		return a

	def conect(self):
		if self:
			wsdl= self.wsdl
			try:
				return Client(wsdl)
			except expression as identifier:
				return False
			
		return False
				
	def parser_web(self,diffgram):
		# print "#"*500
		# print diffgram
		res={}
		if not diffgram:
			return res
		
		SaleStatements=[]
		CashStatements=[]
		if 'SaleStatements' in diffgram:
			for p in diffgram.SaleStatements:
				for t in p[1]:
					val={}
					for row in t:
						t=row[1]
						if type(t) in [str,suds.sax.text.Text]:
							t=t.encode('utf-8')
						if t is None:
							t=0
						val.update({row[0]:t})
					SaleStatements.append(val)
		if 'CashStatements' in diffgram:
			for p in diffgram.CashStatements:
				for t in p[1]:
					val={}
					for row in t:
						t=row[1]
						if type(t) in [str,suds.sax.text.Text]:
							t=t.encode('utf-8')
						if t is None:
							t=0
						val.update({row[0]:t})
					CashStatements.append(val)	
		res.update({'SaleStatements':SaleStatements,'CashStatements':CashStatements})
		return res
