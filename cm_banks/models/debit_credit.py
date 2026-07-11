# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
import locale
import pytz
from odoo.tools.translate import _
import time
from odoo.exceptions import UserError, ValidationError

class debit_credit(models.Model):
	_order = 'date desc'
	_name = 'debit.credit'
	_description='Bancos: Debitos y Creditos'
	_inherit = ['mail.thread']
	_rec_name="number"

	_track = {
		'state': {'debit_credit.debit_credit_state_change': lambda self: True},
		'total': {'debit_credit.debit_credit_total_change': lambda self: True},
	}

	@api.model
	def _get_user_default(self):
		return self.env.user.id

	account_analytic_id = fields.Many2one('account.analytic.account', string="Cuenta Analitica")
	analytic_account_ids = fields.Many2many('account.analytic.account', string="Cuentas Analiticas")
	move_id = fields.Many2one('account.move', string='Asiento', copy=False)
	journal_id = fields.Many2one('account.journal', string='Diario', required=True )
	require_analytic_account=fields.Boolean(string="require analytic account")
	name = fields.Text(string='Circular')
	date = fields.Date(string='Fecha',  index=True, help="Fecha efectiva del asiento contable",default=lambda *a: time.strftime('%Y-%m-%d') )
	amount = fields.Char(compute='_get_totald',string='Total Importe')
	amountdebit = fields.Char(compute='_get_totaldebit',string='Total Debito')
	amountcredit = fields.Char(compute='_get_totalcredit',string='Total Credito')
	amounttext = fields.Char(compute='_get_totalt',string='Total Letras')
	total = fields.Float(string='Total',required=True,tracking=True)
	template_id = fields.Many2one('banks.template', string='Plantillas')
	pay_comp_currency = fields.Boolean(string='Pagar en moneda de la empresa')
	linked_voucher = fields.Boolean(string='Enlazar voucher')
	voucher_id = fields.Many2one('account.payment', string='Documento', copy=False)
	# mcheck_mcheck_id = fields.Many2one('mcheck.mcheck', string='Cheque', copy=False)
	total_equivalent = fields.Float(compute='_get_equivalent', string='Total(Moneda de la empresa)')
	currency = fields.Float(string='Tasa de cambio', digits=(12,4))
	jour_company_id = fields.Integer(string='Empresa')
	was_unreconcilied = fields.Boolean(string='Desconciliar',copy=False)
	doc_type = fields.Selection([('debit','Debito'),('credit','Credito')], string='Tipo',default='debit')
	tax_amount = fields.Float(string='Impuesto', digits='Account')
	rest_credit = fields.Float(string='Debito Faltante',compute='_compute_rest_credit')
	actual_comp_rate = fields.Float(string='Tasa de empresa')
	actual_sec_curr_rate = fields.Float(string='Tasa en moneda secundaria') #date of the anulation of the check
	number = fields.Char(string='Numero', default="Borrador", copy=False)
	user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
	same_currency = fields.Boolean(string="Misma moneda")
	obs=fields.Text(string='Obs')
	type=fields.Selection([
		('sale','Ventas'),
		('purchase','Compras'),
		('payment','Pagos'),
		('receipt','Recibos'),
		], string='Tipo por defecto',default="payment")		 
	mcheck_ids = fields.One2many('debit.credit.name', 'debit_credit_id', string="Lineas de Debito y Credito",copy=True)
	move_ids = fields.One2many('account.move.line','credit_debit_id',string="Movimientos")
	state=fields.Selection(
	    [('draft','Borrador'),
	     ('validated','Validado'),
	     ('anulated','Anulado'),
	    ], string='Estado', 
	    help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Voucher. \
	                \n* The \'Validated \' when validated', tracking=True, default='draft')
	for_founds = fields.Boolean(string="Para Fondos")
	account_found_id = fields.Many2one('account.account',string="Cuenta de Fondos")
	anulation_date = fields.Date(string="Fecha de Anulación")

	def _get_totald(self):
		result = {}
		total=0
		totald=0
		totalc=0				
		for mcheck in self:
			if len(mcheck.mcheck_ids) > 0:
				for lines in mcheck.mcheck_ids:
					total+=lines.amount
					if lines.type=='dr':
						totald+=lines.amount
					if lines.type=='cr':
						totalc+=lines.amount
			mcheck.amount=self.addComa('%.2f'%(totald-totalc))
		return True	

	@api.onchange('journal_id')
	def _get_same_currency(self):
		same = True
		if self.journal_id.currency_id:
			if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
				same = False
		self.same_currency = same

	def _get_totaldebit(self):
		result = {}
		totald=0
		for mcheck in self:
			if len(mcheck.move_ids) > 0:
				for lines in mcheck.move_ids:
					totald+=lines.debit
			mecheck.amountdebit=self.addComa('%.2f'%(totald))
		return True

	def _get_totalcredit(self):
		result = {}
		for mcheck in self:
			totalc=0
			if len(mcheck.move_ids) > 0:
				for lines in mcheck.move_ids:
					totalc+=lines.credit
			mcheck.amountcredit=self.addComa('%.2f'%(totalc))
		return True	

	def _get_totalt(self):
		result = {}
		total=0
		totald=0
		totalc=0				
		for mcheck in self:
			if len(mcheck.mcheck_ids) > 0:
				for lines in mcheck.mcheck_ids:
					total+=lines.amount
					if lines.type=='dr':
						totald+=lines.amount
					if lines.type=='cr':
						totalc+=lines.amount
			if(mcheck.journal_id.currency_id):
				a = self.env['mcheck.mcheck'].to_word(totald-totalc,mcheck.journal_id.currency_id.name)
			else:
				a = self.env['mcheck.mcheck'].to_word(totald-totalc,'HNL')
			result[mcheck.id]=a
		return result

	@api.depends('total','journal_id','date')
	def _get_equivalent(self):
		result={}
		for mcheck in self:
			mcheck.total_equivalent = self._from_to_company_currency(mcheck.total, mcheck.journal_id.currency_id.id, True, mcheck.date)
		return True

	def _from_to_company_currency(self, amount, to_currency_id, opt, date):
		self = self.with_context(date=date)
		company_currency = self.env.user.company_id.currency_id
		from_currency = company_currency

		if to_currency_id:
			from_currency = self.env['res.currency'].browse(to_currency_id)

		if opt:
			# Convertir de "from_currency" a "company_currency"
			return from_currency._convert(amount, company_currency, self.env.company, date, True)
		else:
			# Convertir de "company_currency" a "from_currency"
			return company_currency._convert(amount, from_currency, self.env.company, date, True)

	@api.onchange('date','journal_id')
	def _get_currency(self):
		comp_rate = False
		for dc in self:
			date1 = dc.date
			if dc.journal_id.currency_id:
				user_obj = self.env.user
				if not dc.journal_id.currency_id.id == user_obj.company_id.currency_id.id:
					comp_rate = 1/user_obj.company_id.currency_id._get_conversion_rate(user_obj.company_id.currency_id, dc.journal_id.currency_id, self.env.company, date1)
				else:
					comp_rate = 1/dc.journal_id.currency_id.rate
			dc.currency = comp_rate

	@api.depends('mcheck_ids.amount', 'total','doc_type' )
	def _compute_rest_credit(self):
		tot_lined = 0
		tot_linec = 0
		for lines in self.mcheck_ids:
			if lines.type=='dr':
				tot_lined+=float(round(lines.amount,2))
			elif lines.type=='cr':
				tot_linec+=float(round(lines.amount,2))
			else:
				tot_linec+=0
				tot_lined+=0
		equevalent = float(round(self._from_to_company_currency(self.total,self.journal_id.currency_id.id,True,self.date),2))
		total = 0
		lined = 0
		linec = 0
		if self.pay_comp_currency:
			total = float(round(self._from_to_company_currency(self.total,self.journal_id.currency_id.id,True,self.date),2))
		else:
			total = float(round(self.total,2))
		if self.doc_type == 'debit':
			self.rest_credit = float(round(total-(tot_lined-tot_linec),2))
		elif self.doc_type in ['credit','deposit']:
			self.rest_credit = float(round(total-(tot_linec-tot_lined),2))
		else:
			self.rest_credit = 0
		self.total_equivalent = float(round(equevalent,2))

	@api.onchange('journal_id','doc_type')
	def onchange_journal(self):
		journalid = self.journal_id.id
		doc_type = self.doc_type
		date = self.date
		if doc_type is None or doc_type is False or journalid is False:
			msj=_("Seleccione un tipo y un diario")
		
		if self.journal_id and self.doc_type:
			if self.journal_id.sequence_ids:
				sequence_id = self.journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == self.doc_type)
				if not sequence_id:
					msj=_("Advertencia! Por favor cree una secuencia bancaria con el codigo bancario '" + doc_type + "' o agregue una secuencia para este diario con el codigo bancario '" + doc_type + "'")
					return { 'value' :{'msg' : msj}}

	def action_validate(self):
		corrency_rate = 0.0
		model_currency_rate = None
		decimal_precision = self.env['decimal.precision']
		dec_prec = decimal_precision.search([('name' , '=', 'Account' )])
			
		curr_rates = {}
		curr_rates = self.calculate_curr_rates()
		currency_rate = curr_rates['company_curr_rate']
		currency_id = curr_rates['company_curr_id']
		for mcheck in self:
			obj_user = self.env.user
			obj_company = self.env.user.company_id

			if len(mcheck.mcheck_ids) > 0:
				total=0
				totald=0
				totalc=0
				flag=True
				select_journal_currency_id = curr_rates['journal_curr_id']#the currency of the journal selected, if it dosent have it, it will see if the default account have a currency, in defect it will be the default company currency
				if select_journal_currency_id:#if there is a secundary currency, brings the curency rate for this currency
					select_journal_currency_rate = 1/curr_rates['journal_curr_rate']#rate of the currently selected journal				
				else: #if there was not a secundary currency, wi will use the ones that la compania usa
					select_journal_currency_rate = currency_rate 
					select_journal_currency_id = currency_id
				for line in mcheck.mcheck_ids:
					total += line.amount
					if line.amount <= 0:
						flag = False
					if line.type == 'dr':
						totald += line.amount
					if line.type == 'cr':
						totalc += line.amount
				
				totalc_curr = 0
				totald_curr = 0
				totald = 0
				totalc = 0
				lines_array = []
				name = "/"
				if mcheck.number == 'Borrador':
					mcheck.number = self.update_sequence(mcheck.journal_id, mcheck.doc_type) 
						
				if mcheck.number:
					if self.existe_number(mcheck.number):
						raise UserError(_("Este número pertenece a un cheque validado, no puede crear artículos de diario con el mismo número") )
					else:
						name = mcheck.number

				amove_obj = self.env['account.move']
				amovedata = {
					'journal_id': mcheck.journal_id.id,
					'name': name,
					'internal_number': name,
					'date': mcheck.date,
					'move_type': 'entry',
					'ref': mcheck.name,
					# 'period': account_period_obj.id
				}			
				seq_obj = self.env['ir.sequence']
				move_id = amove_obj.create(amovedata)

				mline_obj = self.env['account.move.line']
				total_acumulado_no_curr = 0
				for lines in mcheck.mcheck_ids:
					if not lines.name:
						self.write({'mcheck_ids': [(1, lines.id, {'name': mcheck.name})]})

					lines_col = self.dict_col(lines)
					lines_col['move_id'] = move_id.id
					lines_col['name'] = lines.name or mcheck.name
					if lines.account_id.account_type == 'expense':
						if not lines.budget_account_id or not lines.process_id or not lines.source_id:
							raise ValidationError("Debe agregar los datos de presupuesto para poder avanzar")

						lines_col['analytic_account_id'] = lines.budget_account_id.id
						lines_col['activity_id'] = lines.process_id.id
						lines_col['source_id'] = lines.source_id.id

					
					if lines.type == 'dr':
						lines_col['credit'] = 0
						if not mcheck.pay_comp_currency:
							lines_col['debit'] = round((lines.amount * select_journal_currency_rate)*currency_rate,dec_prec.digits)
						else:
							lines_col['debit'] = lines.amount							
						totald += lines_col['debit']
						if select_journal_currency_id == currency_id:#si el currency de 
							totald_curr += lines_col['debit']
							total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma
						else:
							lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*select_journal_currency_rate#shame on me, hahahaha 1(x/y)y=x
							if mcheck.pay_comp_currency:
								lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,mcheck.journal_id.currency_id.id,False,mcheck.date) 
								totald_curr += lines_col['amount_currency']
								total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma
							else:
								totald_curr += lines.amount
							lines_col['currency_id'] = select_journal_currency_id
					else:
						lines_col['debit'] = 0
						if not mcheck.pay_comp_currency:
							lines_col['credit'] = round(((lines.amount * select_journal_currency_rate)*currency_rate),dec_prec.digits)
						else:
							lines_col['credit'] = lines.amount							
						totalc += lines_col['credit']  #total of debit multiplicated by default
						if select_journal_currency_id == currency_id:
							totalc_curr += lines_col['credit']
							total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma
						else:
							lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*select_journal_currency_rate*(-1)
							if mcheck.pay_comp_currency:
								lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,mcheck.journal_id.currency_id.id,False,mcheck.date)*(-1)
								totalc_curr += abs(lines_col['amount_currency'])
								total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma	
							else:
								totalc_curr += lines.amount								
							lines_col['currency_id'] = select_journal_currency_id
					lines_col['move_id'] = move_id.id
					lines_col['date'] = mcheck.date
					lines_col['credit_debit_id'] = mcheck.id
					
					lines_array.append(lines_col)
				mline_data = {}
				if mcheck.account_analytic_id.id:
					distribution_analytic = {str(self.account_analytic_id.id): 100.0}
					mline_data['analytic_distribution'] = distribution_analytic
				mline_data['move_id'] = move_id.id
				mline_data['name'] = mcheck.name

				mline_data['account_id'] = mcheck.journal_id.default_account_id.id
				if mcheck.for_founds:
					mline_data['account_id'] = mcheck.account_found_id.id

				if mcheck.doc_type == 'debit':
					mline_data['credit'] = totald-totalc#correct
					mline_data['debit'] = 0
				else:
					mline_data['credit'] = 0
					mline_data['debit'] = totalc-totald#correct
				mline_data['date'] = mcheck.date
				if not (currency_id == select_journal_currency_id):
					mline_data['currency_id'] = select_journal_currency_id
					# mline_data['amount_currency'] = ((totald_curr-totalc_curr) * select_journal_currency_rate * select_journal_currency_rate)*(-1)
					mline_data['amount_currency'] = (totald_curr-totalc_curr)*(-1)
				
				difference = 3.1415
				if mcheck.pay_comp_currency:
					comp_curr = self.env['res.currency'].browse(self.env['res.users'].browse(uid).company_id.currency_id.id)
					doc_curr = mcheck.journal_id.currency_id or comp_curr
					compare = self.env["res.currency"]._compute(doc_curr,comp_curr, mcheck.total,round=True)
					#difference = float(round(compare,2)) - float(round(self.pool.get("res.currency")._compute(cr, uid,  doc_curr,comp_curr, (totald_curr-totalc_curr),round=True,context=context),2))
										
					difference = float(round(compare,2)) - abs(float(round(total_acumulado_no_curr,2)))
					if mcheck.doc_type == 'credit':
						difference = float(round(compare,2)) - abs(float(round(total_acumulado_no_curr,2)))
				else:
					compare = mcheck.total
					difference = float(round(mcheck.total,2)) - float(round(totald_curr-totalc_curr,2))
					if mcheck.doc_type == 'credit':
						difference = float(round(mcheck.total,2))-float(round((totalc_curr-totald_curr),2))
				
				if difference != 0:
					raise UserError(_('Aun tiene una diferencia de '+str(difference)+" intente solucionarlo"))
				mline_data['credit_debit_id'] = mcheck.id

				#line_id= mline_obj.create(mline_data)
				lines_array.append(mline_data)
				for lines2 in lines_array:
					mline_obj.with_context(check_move_validity=False).create(lines2)
					
				if currency_id == select_journal_currency_id:
					select_journal_currency_rate = False
				dcr_pool = self.env['debit.credit']
				if not mcheck.was_unreconcilied:
					# n = self.journal_number(mcheck.journal_id.id,mcheck.doc_type)
					nids = dcr_pool.search([('number', '=', self.number),('state' , '!=', 'draft')])
					if len(nids) > 0:
						raise UserError(_("El número debe ser único para los débitos o créditos, puede que tenga que comprobar la secuencia de su diario") )
					# self.update_sequence(mcheck.journal_id, mcheck.doc_type)
					
				else:
					n = mcheck.number
					nids = dcr_pool.search([('number', '=', n),('state' , '!=', 'draft')])
					if len(nids) > 0:
						raise UserError(_("El número debe ser único para los débitos o créditos, puede que tenga que comprobar la secuencia de su diario") )
						
				jour_comp_id = None
				if mcheck.journal_id.company_id.id:
					jour_comp_id = mcheck.journal_id.company_id.id
				else:
					jour_comp_id = self.env['res.user'].browse(self.env.uid).company_id.id

				if move_id:
					move_id.action_post()
				
				return self.write({'state':'validated', 'move_id':move_id.id, 'actual_comp_rate': currency_rate,'actual_sec_curr_rate': select_journal_currency_rate, 'jour_company_id' : jour_comp_id })
		else:
			raise UserError(_("Seleccione mas de una linea") )

	def reset_to_draft(self):
		self.write({'state':'draft'})

	def calculate_curr_rates(self):
		company_currency = None
		journal_currency = None
		obj_user = self.env.user
		obj_company = obj_user.company_id
		for mcheck in self:
			company_currency = obj_company.currency_id.with_context(date=mcheck.date)
			if mcheck.journal_id.currency_id:
				journal_currency = mcheck.journal_id.currency_id.with_context(date=mcheck.date)
				if company_currency and journal_currency: 
					return {'company_curr_id' : company_currency.id , 'company_curr_rate' : company_currency.rate ,'journal_curr_id': journal_currency.id, 'journal_curr_rate': journal_currency.rate}
				else:
					raise UserError(_("Operation was not finished, Try Again") )
			else:
				if company_currency:
					return {'company_curr_id' : company_currency.id , 'company_curr_rate' : company_currency.rate ,'journal_curr_id': None, 'journal_curr_rate': None}
				else:
					raise UserError(_("Operation was not finished, Try Again") )

	def existe_number(self,number):
		mcheck_pool = self.env['debit.credit']
		mids = mcheck_pool.search([('state','=','validated')])
		for mcheck in mids:	
			if mcheck.number == number:
				return True
		return False

	def dict_col(self,lines):
		lines_col={}
		lines_col['account_id']=lines.account_id.id
		lines_col['partner_id']=lines.partner_id.id
		if lines.chqmanalitics:
			distribution_line = {str(lines.chqmanalitics.id): 100.0}
			lines_col['analytic_distribution'] = distribution_line
		return lines_col

	def update_sequence(self,journal_id, doc_type):
		sequence_id = journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == doc_type)
		if sequence_id:
			return sequence_id.next_by_id()
		else:
			raise ValidationError('No existe una secuencia configurada para el tipo %s en el diario %s, configure una para poder validar'%(doc_type, journal_id.name))

	def _get_sequence(self, journalid, doc_type):
		journal_obj = self.env['account.journal']
		diario = journal_obj.search([('id','=',journalid)])
		seq_id = None
		have_multi=False
		for sq in diario.sequence_ids:
			have_multi = True
			if sq.code2.name == doc_type:
				seq_id = sq.id
		return {'result' : have_multi, 'seq_id' : seq_id}

	def anulate_draft_voucher(self):
		# if not self.was_unreconcilied:
		# 	self.update_sequence(self.journal_id.id, self.doc_type)
		self.write({'state':'anulated', 'anulation_date' : self.date, 'was_unreconcilied':True})

	def set_as_template(self):
		if not self.id: return []
		dc=self
		return {
			'name':_("Enviar como Plantilla"),
			'view_mode': 'form',
			'view_type': 'form',
		   	'res_model': 'banks.template',
		    	'type': 'ir.actions.act_window',
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]',
		    	'context': {'doc_id' : self.id, 'doc_type': dc.doc_type , 'hide_buttons':True}
			}

	def unreconciliate_debit(self):
		if self.move_id:
			self.move_id.button_cancel()
			self.move_id.unlink()
		
		res = {
		    'state': 'draft',
		    'move_id': False,
		    'was_unreconcilied': True ,
		}
		self.write(res)
		# self._update_draft(journal_id, doc_type)
		return True

class mcheck_name(models.Model):
	_name='debit.credit.name'
	_description = "Bancos: Lineas de Debitos y Creditos"
		
	debit_credit_id = fields.Many2one('debit.credit', string='Debito y Credito')
	account_id = fields.Many2one('account.account', string='Cuenta', required=True)
	name = fields.Char(string='Descripcion')
	amount = fields.Float(string='Monto', digits='Account',copy=True)
	chqmanalitics = fields.Many2one("account.analytic.account", string="Check Misc Analiticos")
	type = fields.Selection([('dr','Debito'),('cr','Credito')], string='Dr/Cr',default=lambda self: 'dr' if self._context and self._context['type'] and self._context['type']=='debit' else 'cr')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	source_id = fields.Many2one('crossovered.source_expenditure', string="Fuente de Financiamiento")
	process_id = fields.Many2one('crossovered.activity', string="Proceso")
	budget_account_id = fields.Many2one('account.budget.account', string='Cuenta Presupuesto')
	fbudget_line_ids = fields.Many2many("account.budget.account", related="account_id.fbudget_line_ids")
	factivity_ids = fields.Many2many("crossovered.activity", related="account_id.factivity_ids")


	@api.onchange('account_id')
	def onchange_account_id_budget(self):
		self.budget_account_id = False
		self.source_id = False
		self.process_id = False
		if self.account_id and self.account_id.account_type == 'expense':
			if len(self.factivity_ids) > 0 and len(self.fbudget_line_ids) > 0:
				domain = [('move_type','=','gasto')]
				self.source_id = self.env.get("crossovered.source_expenditure").search(domain,limit=1).id
			if len(self.factivity_ids) == 1:
				self.process_id = self.factivity_ids.id
			if len(self.fbudget_line_ids) == 1:
				self.budget_account_id = self.fbudget_line_ids.id