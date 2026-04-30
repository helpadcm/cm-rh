# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import time
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class banks_deposits(models.Model):
	_name = "banks.deposit"
	_description = 'Depositos Bancarios'
	_inherit = ['mail.thread']
	_rec_name="number"
	_order = 'number desc, date desc'
	_track = {
		'state': {
			'banks_deposit.banks_deposit_state_change': lambda self, cr, uid, obj, context=None: True,
			},
	'total': {
			'banks_deposit.banks_deposit_total_change': lambda self, cr, uid, obj, context=None: True,
			},
	}

	@api.model
	def _get_user_default(self):
		return self.env.user.id

	move_id = fields.Many2one('account.move', string='Entrada Contable', copy=False)
	journal_id = fields.Many2one('account.journal', string='Diario', required=True )
	name = fields.Text(string='Circular', required=True)
	date = fields.Date(string='Fecha',  index=True, help="Fecha efectiva para entradas contables", default=lambda *a: time.strftime('%Y-%m-%d'))
	active = fields.Boolean("Activo", default=True)
	amount = fields.Char(compute='_get_totald', string='Total')
	amountdebit = fields.Float(compute='_get_totaldebit', string='Total Debito')
	amountcredit = fields.Char(compute='_get_totalcredit',string='Total Credito')
	amounttext = fields.Char(compute='_get_totalt', string='Total txt')
	total = fields.Float(string='Monto Total', required=True , tracking=True)
	currency = fields.Float(string='Tasa de cambio', digits=(12,4))
	jour_company_id = fields.Integer(string='Compañia')
	was_unreconcilied = fields.Boolean(string='Desconciliado')
	is_customer_deposit = fields.Boolean(string='Es depósito de cliente')
	doc_type=fields.Selection([('deposit','Deposito')], string='Tipo', default='deposit')
	tax_amount=fields.Float(string='Impuesto', digits='Account')
	msg = fields.Char(compute='_get_msg', store=False)
	rest_credit = fields.Float(string='Debito faltante', compute='_compute_rest_credit')
	pay_comp_currency = fields.Boolean(string='Pagar en moneda de la empresa')
	total_equivalent = fields.Float(compute='_get_equivalent', string='Total(Moneda de empresa)')
	actual_comp_rate = fields.Float(string='Tasa de la empresa')
	actual_sec_curr_rate = fields.Float(string='Tasa moneda secundaria actual') #date of the anulation of the check
	number = fields.Char(string='Numero', default="Borrador")
	user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
	anulation_date = fields.Date(string="Fecha de anulacion")
	same_currency = fields.Boolean(string="Misma moneda")
	obs = fields.Text('Obs')
	type = fields.Selection([
		('sale','Ventas'),
		('purchase','Compras'),
		('payment','Pagos'),
		('receipt','Recibos'),
		], string='Tipo por defecto', default='payment')
	mcheck_ids = fields.One2many('banks.deposit.name','mcheck_id',string="Deposito",copy=True)
	deposits = fields.One2many('account.payment', 'deposit_id', string="Lineas de deposito")
	move_ids = fields.One2many('account.move.line', 'deposit_id', string="Apuntes Contables")
	state=fields.Selection(
		[('draft','Borrador'),
		('validated','Validado'),
		('anulated','Anulado'),
		], string='Estado', 
		help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Voucher. \
					\n* The \'Validated \' when validated' , tracking=True, default='draft')

	def _get_totald(self):
		for mcheck in self:
			totald = 0
			totalc = 0
			if len(mcheck.mcheck_ids) > 0:
				for lines in mcheck.mcheck_ids:
					if lines.type == 'dr':
						totald += lines.amount
					if lines.type == 'cr':
						totalc += lines.amount
			mcheck.amount = '{0:,.2f}'.format(totald - totalc)
		return True	

	def _get_totaldebit(self):
		for mcheck in self:
			totald = 0				
			if len(mcheck.move_ids) > 0:
				totald = sum(mcheck.move_ids.mapped('debit'))
			mcheck.amountdebit = '{0:,.2f}'.format(totald)
		return True	

	def _get_totalcredit(self):
		totalc=0				
		for mcheck in self:
			if len(mcheck.move_ids) > 0:
				totald = sum(mcheck.move_ids.mapped('credit'))
			mcheck.amountcredit = '{0:,.2f}'.format(totalc)
		return True

	def _get_totalt(self):
		for dep in self:
			totald = 0
			totalc = 0				
			if len(dep.mcheck_ids) > 0:
				for lines in dep.mcheck_ids:
					if lines.type == 'dr':
						totald += lines.amount
					if lines.type == 'cr':
						totalc += lines.amount
			if(dep.journal_id.currency):
				a = self.env.get('mcheck.mcheck').to_word(abs(totald-totalc), dep.journal_id.currency_id.name)
			else:
				a = self.env.get('mcheck.mcheck').to_word(abs(totald-totalc), 'HNL')
			dep.amounttext = a
		return True

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

	@api.onchange('journal_id')
	def _get_same_currency(self):
		same = True
		if self.journal_id.currency_id:
			if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
				same = False
		self.same_currency = same

	@api.depends('mcheck_ids.amount', 'total', 'doc_type', 'deposits.amount' )
	def _compute_rest_credit(self):
		for dep in self:
			tot_lined = 0
			tot_linec = 0
			for lines in dep.mcheck_ids:
				if lines.type == 'dr':
					tot_lined += float(round(lines.amount,2)) 
				elif lines.type == 'cr':
					tot_linec += float(round(lines.amount,2))
			t = 0
			if len(dep.deposits) > 0:
				for l in dep.deposits:
					t += float(round(l.amount,2))

			if dep.pay_comp_currency:
				t = float(round(dep._from_to_company_currency(t,dep.journal_id.currency_id.id, True, dep.date), 2))
				dep.rest_credit = float(round( dep._from_to_company_currency(dep.total, dep.journal_id.currency_id.id, True, dep.date)-(t+(tot_linec-tot_lined)), 2))
			else:
				dep.rest_credit = float(round(dep.total, 2))-(float(round(t, 2))+float(round((tot_linec-tot_lined), 2)))
			dep.total_equivalent = float(round(dep._from_to_company_currency(dep.total, dep.journal_id.currency_id.id, True, dep.date), 2))
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

	@api.depends('total','journal_id','date')
	def _get_equivalent(self):
		for deposit in self:
			deposit.total_equivalent = self._from_to_company_currency(deposit.total, deposit.journal_id.currency_id.id, True, deposit.date)
		return True

	def _calculate_number(self):
		for mcheck in self:
			mcheck.number_calc = mcheck.number
		return True

	def action_validate(self):
		corrency_rate = 0.0
		model_currency_rate = None
		decimal_precision = self.env.get('decimal.precision')
		dec_prec = decimal_precision.search([('name' , '=', 'Account' )])
			
		curr_rates={}
		curr_rates = self.calculate_curr_rates()
		currency_rate = curr_rates['company_curr_rate']
		currency_id = curr_rates['company_curr_id']
		select_journal_currency_id = curr_rates['journal_curr_id']#the currency of the journal selected, if it dosent have it, it will see if the default account have a currency, in defect it will be the default company currency
		
		if select_journal_currency_id:#if there is a secundary currency, brings the curency rate for this currency
			select_journal_currency_rate = 1/curr_rates['journal_curr_rate']#rate of the currently selected journal				
			#select_journal_currency_name = curr_rates['company_curr_rate']
		else: #if there was not a secundary currency, wi will use the ones that la compania usa
			select_journal_currency_rate = currency_rate 
			select_journal_currency_id = currency_id
		
		for mcheck in self:
			obj_company = self.env.user.company_id
			if len(mcheck.mcheck_ids) > 0 and len(mcheck.deposits) == 0:
				total = 0
				totald = 0
				totalc = 0
				flag = True
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
				move_id = self.deposit_create_contability(True,dec_prec,currency_rate,currency_id,select_journal_currency_rate,select_journal_currency_id)
				
				if currency_id == select_journal_currency_id:
					select_journal_currency_rate = False
				for lin in mcheck.mcheck_ids:
					if not lin.name:
						new_name = mcheck.name
						mcheck.write({'mcheck_ids': [(1,lin.id,{'name':new_name})]})
				
				n = mcheck.number
				jour_comp_id = None
				if mcheck.journal_id.company_id.id:
					jour_comp_id = mcheck.journal_id.company_id.id
				else:
					jour_comp_id= self.env.get('res.user').browse(self.env.uid).company_id.id
				return self.write({'state':'validated','number':n,'move_id':move_id, 'actual_comp_rate': currency_rate,'actual_sec_curr_rate': select_journal_currency_rate, 'jour_company_id' : jour_comp_id })
			else:
				t_dep = 0
				for d in self:
					jounals_curr = []
					for v in d.deposits:
						if v.journal_id.currency_id.id not in jounals_curr:
							jounals_curr.append(v.journal_id.currency_id.id)
						if len(jounals_curr)  >= 2 :
							raise UserError(_("In Client Payments there are journals with diferent currency"))
					for v in d.deposits:
						if v.journal_id.currency_id.id  != d.journal_id.currency_id.id:
							raise UserError(_("The selected journal currency is diferent than Payment's journal currency"))
						else:
							break
					params = {}
					params = dict(params or {})
					if len(d.deposits) <= 0:
						raise UserError(_("select more than one line in Client payment or in deposit lines") )
					else:	
						move_id,com_line_tot = self.create_lines_by_client_payment(dec_prec,currency_rate,currency_id,select_journal_currency_rate,select_journal_currency_id)
										
					tot = 0
					for c in d.deposits:
						tot += float(round(c.amount,2))
					tot_dep = tot
					tot += float(round(com_line_tot,2))
					diference = 0
					if d.pay_comp_currency:
						tot_equevalent = float(round(self._from_to_company_currency(d.total,d.journal_id.currency_id.id,True,d.date)[0],2))
						tot_dep = float(round(self._from_to_company_currency(tot_dep,d.journal_id.currency_id.id,True,d.date)[0],2))
						lines_tot = float(round(self._from_to_company_currency(d.total,d.journal_id.currency_id.id,True,d.date)[0],2))
						diference = float(round(tot_equevalent,2)) - float(round((com_line_tot + tot_dep),2))
					else:
						diference = float(round(d.total,2)) - float(round(tot,2))
					if diference != 0:
						raise UserError(_('The difference between Clients payment sum and Deposits Lines sum is '+str(diference)),_("It must be cero"))
					else:
						number = self.validation_number_update_drafts(self.ids)
						self.update_vouchers(self.ids)
						return self.write({'state':'validated','number':number,'move_id':move_id})

	def calculate_curr_rates(self):
		company_currency = None
		journal_currency = None
		obj_company = self.env.user.company_id
		for mcheck in self:
			company_currency = obj_company.currency_id.with_context(date=mcheck.date)
			if mcheck.journal_id.currency_id:
				journal_currency = mcheck.journal_id.currency_id.with_context(date=mcheck.date)
				if company_currency and journal_currency: 
					return {'company_curr_id' : company_currency.id , 'company_curr_rate' : company_currency.rate ,'journal_curr_id': journal_currency.id, 'journal_curr_rate': journal_currency.rate}
				else:
					raise UserError(_("Operacion no finalizada, Intente de nuevo") )
			else:
				if company_currency:
					return {'company_curr_id' : company_currency.id , 'company_curr_rate' : company_currency.rate ,'journal_curr_id': None, 'journal_curr_rate': None}
				else:
					raise UserError(_("Operacion no finalizada, Intente de nuevo") )

	def existe_number(self,number):
		mcheck_env = self.env['mcheck.mcheck']
		voucher_env = self.env['account.payment']
		mids = mcheck_env.search(['&','|','&',('state','!=','draft'),('number','=',number),'&',('state','=','draft'),'&',('number','=',number),('was_unreconcilied','=',True),('id','not in',[self.id])])
		mids2 = voucher_env.search(['|','&',('state','!=','draft'),('name','=',number),'&',('state','=','draft'),'&',('name','=',number),('was_unreconcilied','=',True)])	

		if mids or mids2:
				return True
		return False

	def update_sequence(self,journal_id, doc_type):
		sequence_id = journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == doc_type)
		return sequence_id.next_by_id()

	def deposit_create_contability(self, param,dec_prec,currency_rate,currency_id,select_journal_currency_rate,select_journal_currency_id):
		for dep in self:
			totalc_curr = 0
			totald_curr = 0
			totald = 0
			totalc = 0
			obj_company = dep.journal_id.company_id
			name = "/"
			if dep.number == 'Borrador':
				dep.number = self.update_sequence(dep.journal_id, dep.doc_type) 
			
			if dep.number:
				if self.existe_number(dep.number):
					raise UserError(_("This number belong to a validated Deposit, you can not create journal items with the same number") )
				else:
					name = dep.number

			amove_obj = self.env.get('account.move')
			mline_obj = self.env.get('account.move.line')
			amovedata = {
				'journal_id': dep.journal_id.id,
				'name': name,
				'internal_number': name,
				'date': dep.date,
				'ref': dep.name,
			}
			move_id = amove_obj.create(amovedata)
			lines_array = []
			total_acumulado_no_curr = 0
			for lines in dep.mcheck_ids:
				lines_col = self.dict_col(lines)
				lines_col['move_id'] = move_id.id
				
				lines_col['name'] = lines.name  or dep.name

				if lines.account_id.account_type == 'expense':
					if not lines.budget_account_id or not lines.process_id or not lines.source_id:
						raise ValidationError("Debe agregar los datos de presupuesto para poder avanzar")

					lines_col['analytic_account_id'] = lines.budget_account_id.id
					lines_col['activity_id'] = lines.process_id.id
					lines_col['source_id'] = lines.source_id.id
				
				if lines.type == 'dr':
					lines_col['credit'] = 0
					if not dep.pay_comp_currency:
						lines_col['debit'] = round((lines.amount * select_journal_currency_rate),dec_prec.digits)
					else:
						lines_col['debit'] = lines.amount
					totald += lines_col['debit']
					if select_journal_currency_id == currency_id:#si el currency de 
						totald_curr += lines_col['debit']
						total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma
						lines_col['currency_id'] = currency_id
					else:
						lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*select_journal_currency_rate
						if dep.pay_comp_currency:
							lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,dep.journal_id.currency_id.id,False,dep.date)[0] 
							totald_curr += lines_col['amount_currency']
							total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma
						else:
							totald_curr += lines.amount								
						lines_col['currency_id'] = select_journal_currency_id
													
				else:
					lines_col['debit'] = 0
					if not dep.pay_comp_currency:
						lines_col['credit'] = round((lines.amount * select_journal_currency_rate),dec_prec.digits)
					else:
						lines_col['credit'] = lines.amount						
					totalc += lines_col['credit']  #total of debit multiplicated by default
					if select_journal_currency_id == currency_id:
						totalc_curr += lines_col['credit']
						total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma
						if lines.account_id.currency_id:
							lines_col['currency_id'] = lines.account_id.currency_id.id
							lines_col['amount_currency'] = -self._from_to_company_currency(lines.amount, lines.account_id.currency_id.id, False, dep.date)
						else:
							lines_col['currency_id'] = currency_id
							lines_col['amount_currency'] = -lines.amount
					else:
						lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*(-1)*select_journal_currency_rate
						if dep.pay_comp_currency:
							lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,dep.journal_id.currency_id.id,False,dep.date)[0]*(-1)
							totalc_curr += abs(lines_col['amount_currency'])
							total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma	
						else:
							totalc_curr += lines.amount	
						lines_col['currency_id'] = select_journal_currency_id
				lines_col['move_id'] = move_id.id
				lines_col['date'] = dep.date
				lines_col['deposit_id'] = dep.id
				
				lines_array.append(lines_col)
			mline_data = {
				'move_id': move_id.id,
				'name': dep.name,
				'credit': 0,
				'debit': totalc-totald,
				'date': dep.date,
			}
			if not (currency_id == select_journal_currency_id):
				mline_data['currency_id'] = select_journal_currency_id
				mline_data['amount_currency'] = ((totald_curr-totalc_curr) * (1/select_journal_currency_rate)*select_journal_currency_rate)*(-1)
			mline_data['account_id'] = dep.journal_id.default_account_id.id
			mline_data['deposit_id'] = dep.id
			if param:
				difference = 3.1415
				if dep.pay_comp_currency:
					comp_curr = self.env.get('res.currency').browse(self.env.get('res.users').browse(uid).company_id.currency_id.id)
					doc_curr = dep.journal_id.currency or comp_curr
					self.env.context = dict(self.env.context or {})
					self.env.context.update({'date': dep.date})
					compare = self.env.get("res.currency")._compute(doc_curr,comp_curr, dep.total,round=True)	
					#WAS WORKING difference = float(round(compare,2)) - 	float(round(self.env.get("res.currency")._compute(cr, uid,  doc_curr,comp_curr, (totalc_curr-totald_curr),round=True,context=context),2))	
					difference = float(round(compare,2)) - abs(float(round(total_acumulado_no_curr,2)))		
				else:
					compare = dep.total
					difference = float(round(dep.total,2))-float(round((totalc_curr-totald_curr),2))
				if difference != 0:
					raise UserError(_('you still have '+str(difference)+" Try to make it fit"))
					
			#line_id= mline_obj.create(mline_data)
			lines_array.append(mline_data)

			for lines2 in lines_array:
				#se agrega con el contexto para no verificar el movimiento revisar si permite crear descuadrados
				mline_obj.with_context(check_move_validity=False).create(lines2)

			if move_id:
				move_id.action_post()
				return move_id.id

	def dict_col(self,lines):
		lines_col={
			'account_id': lines.account_id.id,
			'partner_id': lines.partner_id.id,
			'name':  lines.name2,
		}
		if lines.chqmanalitics:
			distribution_line = {str(lines.chqmanalitics.id): 100.0}
			lines_col.update({'analytic_distribution': distribution_line})
		return lines_col

	def reset_to_draft(self):
		self.write({'state':'draft'})

	def unreconciliate_deposit(self):
		for deposit in self:
			if deposit.move_id:
				deposit.move_id.button_draft()
				deposit.move_id.unlink()
		res = {
			'state': 'draft',
			'move_id': False,
			'was_unreconcilied': True
		}
		self.write(res)
		return True

	def anulate_draft_voucher(self):
		for deposit in self:
			self.write({'state':'anulated', 'anulation_date' : deposit.date, 'was_unreconcilied':True})

	# @api.returns('self', lambda value: value.id)
	# def copy(self, default=None):
	# 	default = dict(default or {})
	# 	default['state'] ='draft'
	# 	default['date'] = datetime.now()
	# 	default['number'] = 'Borrador'
	# 	default['was_unreconcilied'] = False
	# 	encabezado = super(banks_deposits, self).copy(default)
	# 	# for line in self.mcheck_ids:
	# 	# 	a = self.env['banks.deposit.name'].create({'mcheck_id': encabezado.id, 'account_id': line.account_id.id, 'name':line.name, 'amount': line.amount, 'chqmanalitics': line.chqmanalitics.id, 'type':line.type})
	# 	return encabezado

	def unlink(self):
		deposits = self
		flag = False
		for deposit in self:
			if deposit.state not in  ['draft'] or deposit.was_unreconcilied:
				flag = True
				
		if flag:
			raise UserError(_("No puede borrar un depósito cuando tiene un estado diferente al Borrador o no ha sido desconciliado!"))
		else:
			return super(banks_deposits, self).unlink()	

	def add_account(self):
		if self.move_id:
			account_id = self.env['account.account'].search([('code','=','102.02')])
			self.unreconciliate_deposit()
			line_id = self.mcheck_ids[0]
			line_id.account_id = account_id.id
			analytic_account_id = self.env['account.analytic.account'].search([('partner_id','=',self.user_id.partner_id.id)])
			if analytic_account_id:
				line_id.chqmanalitics = analytic_account_id.id
			# print ("//////////////////////////////")
			# print (analytic_account_id)
			# if self.move_id:
			# 	for line in self.move_id.line_ids:
			# 		if line.credit > 0:
			# 				distribution_line = {str(analytic_account_id.id): 100.0}
			# 				line.analytic_distribution = distribution_line
			self.action_validate()

class banks_deposit_name(models.Model):
	_name = 'banks.deposit.name'
	_description = "Lineas de deposito"
		
	mcheck_id = fields.Many2one('banks.deposit', string='Deposito')
	account_id = fields.Many2one('account.account', string='Cuenta',required=True)
	name = fields.Char(string='Descripcion')
	name2 = fields.Char(string='Recibo')
	amount = fields.Float(string='Monto', digits='Account',copy=True)
	partner_id = fields.Many2one('res.partner', string='Empresa')
	chqmanalitics = fields.Many2one("account.analytic.account",string="Depositos Analiticos")
	type = fields.Selection([('dr','Debito'),('cr','Credito')], string='Db/Cr',default="cr")
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







