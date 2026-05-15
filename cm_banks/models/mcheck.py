# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
from odoo.exceptions import UserError, ValidationError

UNIDADES = ('', 'UN ', 'DOS ', 'TRES ', 'CUATRO ', 'CINCO ', 'SEIS ', 'SIETE ', 'OCHO ', 'NUEVE ', 'DIEZ ', 'ONCE ', 'DOCE ',
            		'TRECE ', 'CATORCE ', 'QUINCE ', 'DIECISEIS ', 'DIECISIETE ', 'DIECIOCHO ', 'DIECINUEVE ', 'VEINTE ')

DECENAS = ('VENTI', 'TREINTA ', 'CUARENTA ', 'CINCUENTA ', 'SESENTA ',
			'SETENTA ', 'OCHENTA ', 'NOVENTA ', 'CIEN ')

CENTENAS = ('CIENTO ', 'DOSCIENTOS ', 'TRESCIENTOS ', 'CUATROCIENTOS ', 'QUINIENTOS ',
			'SEISCIENTOS ', 'SETECIENTOS ', 'OCHOCIENTOS ', 'NOVECIENTOS ')

MONEDAS = (
	{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
	{'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
	{'country': u'Costa Rica', 'currency': 'CRC', 'singular': u'Colon', 'plural': u'Colones', 'symbol': u'₡'},
	{'country': u'Guatemala Quetzal', 'currency': 'GTQ', 'singular': u'Quetzal', 'plural': u'Quetzales', 'symbol': u'Q'},
	{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
	{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
	{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
	{'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
	{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
	)

class mcheck(models.Model):
	_name = 'mcheck.mcheck'
	_description='Pagos Miscelaneos'
	_inherit = ['mail.thread']
	_rec_name="number"
	_order = 'number desc, date desc' 
	_track = {
        'state': {
            'mcheck_mcheck.mcheck_state_change': lambda self, cr, uid, obj, context=None: True,
       		 },
	 'total': {
            'mcheck_mcheck.mcheck_total_change': lambda self, cr, uid, obj, context=None: True,
       		 },
   	 }

	@api.model
	def _use_creator(self):
		return self.env.user.id
	 
	delivery = fields.Boolean(string="Entregar",default=False)
	date_write_two = fields.Datetime(string='Segunda fecha de escritura')
	move_id = fields.Many2one('account.move', string='Entrada Contable', copy=False)
	journal_id = fields.Many2one('account.journal', string='Diario', required=True )
	name = fields.Text(string='Circular', required=True)
	date = fields.Date(string='Fecha',  index=True, help="Effective date for accounting entries", required=True, default=lambda *a: time.strftime('%Y-%m-%d') )
	amount = fields.Char(compute='_get_totald', string='Total')
	debit_credit_id = fields.Many2one('debit.credit', string='Debito/Credito')#for cancelation with date
	amountdebit = fields.Char(compute='_get_totaldebit', string='Total Debito')
	amountcredit = fields.Char(compute='_get_totalcredit', string='Total Credito')
	pay_comp_currency = fields.Boolean(string='Pagar en moneda de la empresa')
	anulated_contrapartida = fields.Boolean(string='Anular Contrapartida')
	total_equivalent = fields.Float(compute='_get_equivalent', string='Total(Moneda de empresa)')
	amounttext = fields.Char(compute='_get_totalt', string='Total Texto')
	was_unreconcilied = fields.Boolean(string='Desconciliar', default=False)
	has_been_unreconcilied = fields.Boolean(string='Ha sido Desconciliado', default=False)#for showing invalidate draft buttons
	total = fields.Float(string='Total Monto',required=True, tracking=True)
	currency = fields.Float(string='Tasa de cambio', digits=(12,4))
	jour_company_id = fields.Integer(string='Empresa')
	
	template_id = fields.Many2one('banks.template', string='Plantilla')
	doc_type = fields.Selection([
					('check','Cheque'),
					('transference','Transferencia')], string='Tipo de Documento', default='check')
	tax_amount = fields.Float(string='Impuesto', digits='Account')
	reference = fields.Char(string='Pagar a', help="Transaction reference number.", copy=True,required=True)
	identy = fields.Char(string='Identidad', help="Identy", copy=False)
	rest_credit = fields.Float(string='Debito Faltante', compute='_compute_rest_credit')
	commission = fields.Float(string='Comision')
	actual_comp_rate = fields.Float(string='Tasa de empresa')
	actual_sec_curr_rate = fields.Float(string='Tasa real de moneda secundaria')
	anulation_date = fields.Date(string='Fecha de Anulacion', help="Fecha efectiva de anulacion") #date of the anulation of the check
	number = fields.Char(string='Numero',default="Borrador",copy=False)
	obs = fields.Text(string='obs')
	anulation_ref = fields.Many2one('account.move', string='Ref. Anulacion', copy=False)
	# banks_check_book_assoc = fields.Many2one(compute='_calculate_journal_assoc', comodel_name="banks.checkbook", string='Diario de Bancos')
	user_creator = fields.Many2one(default=_use_creator, comodel_name="res.users", string='Usuario')
	op_code = fields.Char(string="Orden de pago")
	same_currency = fields.Boolean(string="Misma moneda")
	type = fields.Selection([
		('sale','Venta'),
		('purchase','Compras'),
		('payment','Pago'),
		('receipt','Recibos'),
		], string='Tipo por defecto', default='payment')
	mcheck_ids = fields.One2many('mcheck.mcheck_name', 'mcheck_id',string="Lineas de Cheque",copy=True)
	move_ids = fields.One2many('account.move.line', 'mcheck_id',string="Movimiento contable en línea de cheque")
	state = fields.Selection(
	    [('draft','Borrador'),
		('validated','Validado'),
	     ('anulated','Anulado'),
	    ], string='Estado', 
	    help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Voucher. \
	                \n* The \'Pro-forma\' when voucher is in Pro-forma status,voucher does not have an voucher number. \
	                \n* The \'Posted\' status is used when user create voucher,a voucher number is generated and voucher entries are created in account \
	                \n* The \'Cancelled\' status is used when user cancel voucher.', tracking=True, default='draft')

	def _get_totald(self):
		result = {}
		totald = 0
		totalc = 0			
		total = 0	
		for mcheck in self:
			if len(mcheck.mcheck_ids) > 0:
				for lines in mcheck.mcheck_ids:
					total += lines.amount
					if lines.type == 'dr':
						totald += lines.amount
					if lines.type == 'cr':
						totalc += lines.amount
			mcheck.amount = '{0:,.2f}'.format(totald-totalc)
		return result

	@api.onchange('journal_id')
	def _get_same_currency(self):
		same = True
		if self.journal_id.currency_id:
			if self.journal_id.currency_id.id != self.env.user.company_id.currency_id.id:
				same = False
		self.same_currency = same

	def _get_totaldebit(self):
		result = {}
		for mcheck in self:
			totald = 0
			if len(mcheck.move_ids) > 0:
				for lines in mcheck.move_ids:
					totald += lines.debit
			mcheck.amountdebit = '{0:,.2f}'.format(totald)

	def _get_totalcredit(self):
		result = {}
		totalc = 0
		for mcheck in self:
			if len(mcheck.move_ids) > 0:
				for lines in mcheck.move_ids:
					totalc += lines.credit
			mcheck.amountcredit = '{0:,.2f}'.format(totalc)

	@api.depends('total','journal_id','date')
	def _get_equivalent(self):
		result = {}
		for mcheck in self:
			mcheck.total_equivalent = self._from_to_company_currency(mcheck.total,mcheck.journal_id.currency_id.id,True,mcheck.date)	
		return True

	def _get_totalt(self):
		result = {}
		total = 0
		totald = 0
		totalc = 0
		for mcheck in self:
			if len(mcheck.mcheck_ids) > 0:
				for lines in mcheck.mcheck_ids:
					total += lines.amount
					if lines.type == 'dr':
						totald += lines.amount
					if lines.type == 'cr':
						totalc += lines.amount
			if(mcheck.journal_id.currency_id):
				a = mcheck.to_word(abs(totald - totalc), mcheck.journal_id.currency_id.name)
			else:
				a = mcheck.to_word(abs(totald - totalc), 'HNL')
			mcheck.amounttext = a

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

	@api.depends('mcheck_ids.amount', 'total')
	def _compute_rest_credit(self):
		for rec in self:
			tot_lined = 0
			tot_linec = 0
			for lines in rec.mcheck_ids:
				if lines.type == 'dr':
					tot_lined += round(lines.amount,2) 
				elif lines.type == 'cr':
					tot_linec += round(lines.amount,2)
				else:
					tot_linec += 0
					tot_lined += 0
			equevalent = rec._from_to_company_currency(rec.total, rec.journal_id.currency_id.id, True, rec.date)
			equevalent = float(round(equevalent,2))
			if rec.pay_comp_currency:
				rec.rest_credit = equevalent - (tot_lined - tot_linec)
			else:
				rec.rest_credit = float(round(rec.total,2)) - float(round((tot_lined - tot_linec),2))
			rec.total_equivalent = equevalent

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

	def to_word(self, number, mi_moneda):
		valor = number
		number = int(number)
		decimal_value = valor - number

		if decimal_value >= 0.5:
			centavos = math.ceil(round(decimal_value, 2) * 100)
		else:
			if (round(decimal_value,2)) == 0.29:
				centavos = 29
			else:
				centavos = int((round(valor-number,2)) * 100)

		#else:
		#    centavos = (round(valor-number,2)) * 100

		if mi_moneda != None:
			for r in MONEDAS:
				if r['currency'] == mi_moneda:
					moneda = r
			#moneda = filter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
			if number < 2:
				moneda = moneda['singular']
			else:
				moneda = moneda['plural']
		else:
			moneda = ""
		converted = ''

		if not (0 < number < 999999999):
			return 'No es posible convertir el numero a letras'

		number_str = str(number).zfill(9)
		millones = number_str[:3]
		miles = number_str[3:6]
		cientos = number_str[6:]

		if(millones):
			if(millones == '001'):
				converted += 'UN MILLON '
			elif(int(millones) > 0):
				converted += '%sMILLONES ' % self.convert_group(millones)

		if(miles):
			if(miles == '001'):
				converted += 'MIL '
			elif(int(miles) > 0):
				converted += '%sMIL ' % self.convert_group(miles)

		if(cientos):
			if(cientos == '001'):
				converted += 'UN '
			elif(int(cientos) > 0):
				converted += '%s ' % self.convert_group(cientos)
		converted += moneda
		if(centavos)>0:
			cents = centavos
			if centavos < 10:
				cents = "0%s"%centavos
			converted+= " con %s/100 Centavos"%cents
		elif(centavos) == 0:
			converted+= " con 00/100 Centavos"

			
		#converted += moneda
		return converted.title()

	def convert_group(self, n):
		output = ''

		if(n == '100'):
			output = "CIEN "
		elif(n[0] != '0'):
			output = CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

		return output

	def anullation_date_load(self):
		view_id_form  = self.env.ref('cm_banks.banks_anullation_date_wizard_form').id
		
		if not self.ids: return []
		
		self.env.context=dict(self.env.context or {})
		
		for m in self:
			self.env.context.update({'date': m.date})
			self.env.context.update({'journal_id': m.journal_id.id})
		
		return {
			'name':_("Fecha de Anulacion"),
			'view_type': 'form',
		   	'res_model': 'anullation_date_wizard',
		    	'type': 'ir.actions.act_window',
			'context': self.env.context,
			'views': [(view_id_form, 'form')],
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]'
			}

	def set_as_template(self):
		mcheck=self
		jour_comp_id =None
		if not self.id: return []
		return {
			'name':_("Usar como Plantilla"),
			'view_mode': 'form',
			'view_type': 'form,tree',
		   	'res_model': 'banks.template',
		    	'type': 'ir.actions.act_window',
			'context': self.env.context,
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]',
		    	'context': {'doc_id' : self.id,'doc_type': mcheck.doc_type, 'hide_buttons':True}
			}
	
	def unreconciliate_mcheck(self):
		for mcheck in self:
			if mcheck.move_id:
				mcheck.move_id.button_cancel()
				mcheck.move_id.unlink()
			res = {
				'state': 'draft',
				'move_id': False,
				'was_unreconcilied': True,
				'has_been_unreconcilied': True,
			}
			mcheck.write(res)
		return True

	def _get_sequence(self,journalid, doc_type):
		seq_id = None
		have_multi = False
		if doc_type == 'mcheck':
			seq_id = journalid.sequence_id.id

		if journalid.sequence_ids:
			have_multi = True
			seq_id = journalid.sequence_ids.filtered(lambda seq: seq.code2.code == doc_type)
		return {'result' : have_multi, 'seq_id' : seq_id}

	def anulate_draft_voucher(self):
		for mcheck in self:	
			mcheck.write({'total':0,'state':'anulated','total':0,'anulation_date' :mcheck.date,'was_unreconcilied':True})
			for line in mcheck.mcheck_ids:
				self.env['mcheck.mcheck_name'].browse(line.id).unlink()

	def update_sequence(self,journal_id, doc_type):
		sequence_id = journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == doc_type)
		if sequence_id:
			if self.number == 'Borrador':
				return sequence_id.next_by_id()
		else:
			raise ValidationError('No existe una secuencia configurada para el tipo %s en el diario %s, configure una para poder validar'%(doc_type, journal_id.name))

	def action_validate(self):
		if self.state!="draft":
			raise UserError(_("El Pago ya fue Validado") )

		context = dict(self.env.context or {})
		currency_rate = 0.0
		model_currency_rate = None
		obj_company = False
		decimal_precision = self.env['decimal.precision']
		dec_prec = decimal_precision.search([('name' , '=', 'Account' )])

		curr_rates={}
		curr_rates = self.calculate_curr_rates()
		currency_rate = curr_rates['company_curr_rate']
		currency_id = curr_rates['company_curr_id']

		for mcheck in self:
			obj_company = self.env.user.company_id
			if len(mcheck.mcheck_ids) > 0:
				total = 0
				totald = 0
				totalc = 0
				flag=True
				select_journal_currency_id = curr_rates['journal_curr_id']#the currency of the journal selected, if it dosent have it, it will see if the default account have a currency, in defect it will be the default company currency
				if select_journal_currency_id:#if there is a secundary currency, brings the curency rate for this currency
					select_journal_currency_rate = 1/curr_rates['journal_curr_rate']#rate of the currently selected journal				
					#select_journal_currency_name = curr_rates['company_curr_rate']
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
				
				if ((totald-totalc) > 0 and flag==True):
					totalc_curr = 0
					totald_curr = 0
					totald = 0
					totalc = 0
					lines_array = []
					name = "/"
					if mcheck.number == 'Borrador':
						mcheck.number = self.update_sequence(mcheck.journal_id, mcheck.doc_type) 
					
					if self.existe_number(mcheck.number): 
						raise UserError(_("This number belong to a validated document, you can not create journal items with the same number") )
					else:						
						name = mcheck.number

					amove_obj = self.env.get('account.move')
					amovedata = {
						'journal_id': mcheck.journal_id.id,
						'name': name,
						'internal_number': name,
						'date': mcheck.date,
						'ref': mcheck.reference					
					}

					move_id = amove_obj.create(amovedata)
					mline_obj = self.env['account.move.line']
					flag2 = True
					total_acumulado_no_curr = 0
					context.update({'date':mcheck.date})
					for lines in mcheck.mcheck_ids:
						lines_col = self.dict_col(lines)
						lines_col['move_id']=move_id.id
						
						lines_col['name'] = lines.name  or mcheck.name

						if lines.account_id.account_type == 'expense':
							if not lines.budget_account_id or not lines.process_id or not lines.source_id:
								raise ValidationError("Debe agregar los datos de presupuesto para poder avanzar")

							lines_col['analytic_account_id'] = lines.budget_account_id.id
							lines_col['activity_id'] = lines.process_id.id
							lines_col['source_id'] = lines.source_id.id
						
						if lines.type == 'dr':
							lines_col['credit']=0
							if not mcheck.pay_comp_currency:
								lines_col['debit'] = round(lines.amount * select_journal_currency_rate, dec_prec.digits)
							else:
								lines_col['debit'] = lines.amount							
							totald += lines_col['debit']
							if select_journal_currency_id == currency_id:#si el currency de 
								lines_col['currency_id'] = currency_id
								totald_curr += lines_col['debit']
								total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma
								lines_col['amount_currency'] = lines.amount
							else:
								lines_col['currency_id'] = mcheck.journal_id.currency_id.id
								lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*select_journal_currency_rate#shame on me, hahahaha 1(x/y)y=x
								if mcheck.pay_comp_currency:
									lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,mcheck.journal_id.currency_id.id,False,mcheck.date) 
									totald_curr += lines_col['amount_currency']
									total_acumulado_no_curr -= lines.amount	#nueva opcion convertir al final la suma							
								else:
									totald_curr += lines.amount
						else:
							lines_col['debit'] = 0
							if not mcheck.pay_comp_currency:
								lines_col['credit'] = round(((lines.amount * (1/select_journal_currency_rate))*currency_rate),dec_prec.digits)
							else:
								lines_col['credit'] = lines.amount							
							totalc += lines_col['credit']  #total of debit multiplicated by default
							
							if select_journal_currency_id == currency_id:
								totalc_curr += lines_col['credit']
								total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma
								lines_col['amount_currency'] = (lines.amount)*-1
							else:
								lines_col['amount_currency'] = (lines.amount * (1/select_journal_currency_rate))*(-1)*select_journal_currency_rate
								if mcheck.pay_comp_currency:
									lines_col['amount_currency'] = self._from_to_company_currency(lines.amount,mcheck.journal_id.currency_id.id,False,mcheck.date,context=context)*(-1)
									totalc_curr += abs(lines_col['amount_currency'])
									total_acumulado_no_curr += lines.amount	#nueva opcion convertir al final la suma							
								else:
									totalc_curr += lines.amount								
								lines_col['currency_id'] = select_journal_currency_id
						
						if lines.account_id.currency_id.id != mcheck.journal_id.currency_id.id:
							from_currency= to_currency = obj_company.currency_id.id 
							if lines.account_id.currency_id.id:
								to_currency = lines.account_id.currency_id.id
							
							if mcheck.journal_id.currency_id.id:
								from_currency = mcheck.journal_id.currency_id.id			
							
							if not lines.account_id.currency_id.id:
								lines_col['currency_id'] = select_journal_currency_id
								# lines_col['amount_currency'] = False
							else:
								lines_col['currency_id'] = lines.account_id.currency_id.id or mcheck.journal_id.currency.id
								currency_amount = self._from_to_company_currency(lines.amount, lines.account_id.currency_id.id, False, mcheck.date)
								if lines.type == 'cr':
									currency_amount = currency_amount * -1
								lines_col['amount_currency'] = currency_amount
						
													
						lines_col['move_id']=move_id.id
						lines_col['date']=mcheck.date
						lines_col['mcheck_id']=mcheck.id
						
						lines_array.append(lines_col)#adding movline to an array
					if mcheck.commission > 0:#for commission lines creation
						
						if mcheck.journal_id.commission_account.id:
							for i in [1,2]:			
								name=mcheck.name or ""
								com_line = {
									'move_id': move_id.id,
									'mcheck_id': mcheck.id,
									'name': '/Commission-' + name,
									'amount_currency': None,
									'currency_id': currency_id
								}
								if i==1:
									
									com_line['account_id'] = mcheck.journal_id.commission_account.id
									if not select_journal_currency_id == currency_id:
										com_line['amount_currency'] = (mcheck.commission * (1/select_journal_currency_rate))*select_journal_currency_rate	
										com_line['currency_id'] = select_journal_currency_id
									else:
										com_line['currency_id'] = currency_id
									com_line['debit'] = round((mcheck.commission * select_journal_currency_rate),dec_prec.digits) 
									com_line['credit'] = 0
								else:
									if mcheck.journal_id.default_account_id:
										com_line['account_id'] = mcheck.journal_id.default_account_id.id
									if not select_journal_currency_id == currency_id:
										com_line ['amount_currency'] = (mcheck.commission * (1/select_journal_currency_rate))*(-1)*select_journal_currency_rate
										com_line ['currency_id'] = select_journal_currency_id
									else:
										com_line['currency_id'] = currency_id
									com_line['debit'] = 0
									com_line['credit'] = round((mcheck.commission * select_journal_currency_rate),dec_prec.digits)
								lines_array.append(com_line)
						else:
							raise UserError(_("The selected journal must have a commission account asociadted if you want to use commissions") )
					
					mline_data = {
						'move_id': move_id.id,
						'name': mcheck.name,
						'credit': totald-totalc,
						'debit': 0,
						'date': mcheck.date
					}
					if not (currency_id == select_journal_currency_id):
						mline_data['currency_id'] = select_journal_currency_id
						mline_data['amount_currency'] = ((totald_curr-totalc_curr) * (1/select_journal_currency_rate)*select_journal_currency_rate)*(-1)
					else:
						mline_data['currency_id'] = currency_id
						mline_data['amount_currency'] = (totald - totalc)*-1

					mline_data['account_id'] = mcheck.journal_id.default_account_id.id
					mline_data['mcheck_id'] = mcheck.id
					difference = 3.1415
					if mcheck.pay_comp_currency:
						context = dict(context or {})
						context.update({'date': mcheck.date})
						comp_curr = self.env.get('res.currency').browse(cr,uid,self.env.get('res.users').browse(cr,uid,uid,context=context).company_id.currency_id.id,context = context)
						doc_curr = mcheck.journal_id.currency or comp_curr
						compare = self.env.get("res.currency")._compute(cr, uid,  doc_curr,comp_curr, mcheck.total,round=True,context=context)
						difference = float(round(compare,2)) - abs(float(round(total_acumulado_no_curr,2)))
						#float(round(self.env.get("res.currency")._compute(cr, uid,  doc_curr,comp_curr, (totald_curr-totalc_curr),round=True,context=context),2))
					else:
						compare = mcheck.total
						difference = float(round(mcheck.total,2))-float(round((totald_curr-totalc_curr),2))
					if difference != 0:
						raise UserError(_('you still have '+str(difference)+" Try to make it fit"))

					line_id= mline_obj.with_context(check_move_validity=False).create(mline_data)
					for lines2 in lines_array:
						mline_obj.with_context(check_move_validity=False).create(lines2)
					
					if currency_id == select_journal_currency_id:
						select_journal_currency_rate = False
					for lin in mcheck.mcheck_ids:
						if not lin.name:
							new_name = mcheck.name
							mcheck.write({'mcheck_ids': [(1,lin.id,{'name':new_name})]})
					mchecks_env = self.env.get('mcheck.mcheck')
					if not mcheck.was_unreconcilied:
						n = mcheck.number
						nids = mchecks_env.search([('number', '=', n),('state' , '!=', 'draft')])
						if len(nids) > 0:
							raise UserError(_("Number most be unique for validated Miscellaneous checks, you may have to check the sequence of you journal") )
					else:
						n = mcheck.number
						nids = mchecks_env.search([('number', '=', n),('state' , '!=', 'draft')])
						if len(nids) > 0:
							raise UserError(_("Number most be unique for validated Miscellaneous checks, you may have to check the sequence of you journal") )
						
					jour_id = mcheck.journal_id.company_id.id
					jour_comp_id = None
					if mcheck.journal_id.company_id.id:
						jour_comp_id = mcheck.journal_id.company_id.id
					else:
						jour_comp_id= self.env.get('res.user').browse(uid).company_id.id
					
					if move_id:
						move_id.action_post()		

					return self.write({'state':'validated','number':n,'move_id':move_id.id, 'actual_comp_rate': currency_rate,'actual_sec_curr_rate': select_journal_currency_rate, 'jour_company_id' : jour_comp_id})
								
				else:
					raise UserError(_("El valor total es 0") )
			else:
				raise UserError(_("Seleccione mas de una linea") )

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

	def reset_to_draft(self):
		for mcheck in self:
			if mcheck.anulated_contrapartida:
				raise UserError(_("No puede regresar este pago a borrador!"))

		self.write({'state':'draft'})

	@api.model
	def dict_col(self,lines):
		lines_col = {
			'partner_id': lines.partner_id.id,
			'account_id': lines.account_id.id
		}
		if lines.chqmanalitics:
			distribution_line = {str(lines.chqmanalitics.id): 100.0}
			lines_col.update({'analytic_distribution': distribution_line})
		return lines_col

	# @api.returns('self', lambda value: value.id)
	# def copy(self, default=None):
	# 	default = dict(default or {})
	# 	default['number'] = 'Borrador'
	# 	default['state'] = 'draft'
	# 	default['reference'] = self.reference
	# 	default['date'] = datetime.now()
	# 	default['was_unreconcilied'] = False
	# 	encabezado = super(mcheck, self).copy(default)
	# 	# for line in self.mcheck_ids:
	# 	# 	a = self.env['mcheck.mcheck_name'].create({'mcheck_id': encabezado.id, 'account_id': line.account_id.id, 'name':line.name, 'amount': line.amount, 'chqmanalitics': line.chqmanalitics.id, 'type':line.type })
	# 	return encabezado

	def cancel_payment(self,anullation_date):
		self.env.context = dict(self.env.context or {})
		if self.env.context.get('active_id') and anullation_date:
			selected_cancel_date = anullation_date#selected date in the wizard for tha cancelation 
			chck_memo = ''
			movec_id = None
			for mcheck in self:
				existe_seq = None 
				if mcheck.doc_type == 'check':
					existe_seq  = self._get_sequence(mcheck.journal_id,'check_cancel')
				else:
					existe_seq  = self._get_sequence(mcheck.journal_id,'transference_cancel')
				
				if existe_seq['seq_id'] == None:
					raise UserError(_("Por favor crea una secuencia para cancelar el tipo de documento seleccionado!"))
			
				check_move_obj = mcheck.move_id
				move_line = self.env['account.move.line']
				move_l_obj = move_line.search([('move_id','=',check_move_obj.id )])
				move_values = {}
				#odoo10 account_period = self.env['account.period']
				#odoo10 account_period_obj = account_period.search(['&','&',( 'date_start','<=', selected_cancel_date),('date_stop', '>=',selected_cancel_date),('special','<>',True),('company_id','=',mcheck.journal_id.company_id.id),('state', '=', 'draft')])
				for obj in check_move_obj:
					move_values['date'] = selected_cancel_date
					move_values['journal_id'] = obj.journal_id.id
					if mcheck.doc_type=='check':
						move_values['name'] = self.journal_number(mcheck.journal_id, 'check_cancel')
					else:
						move_values['name'] = self.journal_number(mcheck.journal_id, 'transference_cancel')
					move_values['ref'] = obj['ref']
					move_values['narration'] = 'Anulacion de pago %s el %s'%(mcheck.number, mcheck.date)
				
				move_id = self.env['account.move'].create(move_values)
				movec_id = move_id.id 
				move_l_values = {}
				move_l_values['date'] = selected_cancel_date
				if self.env.context.get('only_one',False):
					debit_credit = self.env["debit.credit"].browse(self.env.context.get('debit_credit_id',False))
					debit_note_balance = 0
					for line in debit_credit.move_ids:
						if line.account_id.id ==  debit_credit.journal_id.default_account_id.id:
							if line.debit > 0:
								debit_note_balance += line.debit
							else:
								debit_note_balance += line.credit
					debit_note_balance = debit_credit.total
					if debit_note_balance != mcheck.total:
						raise UserError(_("El monto del pago debe ser igual al total del cheque") )
					self.env['debit.credit'].browse(debit_credit.id).write({'linked_voucher':True, 'mcheck_mcheck_id':mcheck.id})
					return self.write({'state':'anulated','debit_credit_id':context.get('debit_credit_id',False),'anulation_date' : context.get('anullation_date',False)})
					 

				if not self.env.context.get('only_one',False):
					for lines2 in move_l_obj:
						move_l_values.update({
							'name': lines2.name,
							'account_id': lines2.account_id.id,
							'mcheck_id': lines2.mcheck_id.id,
							'move_id': move_id.id,
							'currency_id': lines2.currency_id.id,
							'amount_currency': lines2.amount_currency,
						})
			
						if lines2.credit == 0:
							move_l_values.update({
								'debit': 0,
								'credit': lines2.debit,
								'amount_currency': lines2.amount_currency*(-1),
							})
			
						else:
							move_l_values.update({
								'credit': 0,
								'debit': lines2.credit	
							})
						move_l_values['amount_currency'] = lines2['amount_currency']*(-1)
						move_line.with_context(check_move_validity=False).create(move_l_values)
				
				for lin in mcheck.mcheck_ids:
					if lin.name:
						new_name = 'Anulacion de cheque '+str(mcheck.number)
					else:
						new_name = 'Anulacion de cheque '+str(mcheck.number)
					self.write({'mcheck_ids': [(1, lin.id, {'name':new_name})]})
				if mcheck.name:
					chck_memo = mcheck.name
				else:
					chck_memo = 'Anulacion de cheque '+ str(mcheck.number)
				if mcheck.doc_type == 'check':
					self.update_sequence(mcheck.journal_id,'check_cancel')
				else:
					self.update_sequence(mcheck.journal_id,'transference_cancel')
				if move_id:
					move_id.action_post()

			return self.write({'state':'anulated', 'name':chck_memo, 'anulation_date' : anullation_date , 'anulation_ref' : movec_id, 'anulated_contrapartida':True})
		else:
			raise UserError(_("Operacion no finalizada, Intente de nuevo.") )

	def journal_number(self,journalid,doc_type):
		if not journalid == False and doc_type != False:
			self.env.context = dict(self.env.context or {})
			name = "/"
			seq_id = False
			fl = False

			if journalid.sequence_ids:
				seq_id = journalid.sequence_ids.filtered(lambda seq: seq.code2.code == doc_type)
			else:
				return None
		
			if journalid.sequence_id:
				if not journalid.sequence_id.active:
					raise UserError(_('Error de Configuracion !'),_('Por favor active la secuencia del diario seleccionado !'))			
				self.env.context.update({'no_update' : True})
				name = seq_id.next_by_id()
				return  name
			else:
				return None
		else:
			return None

class mcheck_name(models.Model):
	_name = 'mcheck.mcheck_name'
	_description = "Lineas pagos miscelaneos"

	mcheck_id = fields.Many2one('mcheck.mcheck', string='mcheck')
	account_id = fields.Many2one('account.account', string='Cuenta', required=True)
	name = fields.Char(string='Descripcion')
	amount = fields.Float(string='Monto', digits='Account',copy=True)
	chqmanalitics = fields.Many2one("account.analytic.account", string="Analiticas")
	type = fields.Selection([('dr','Debito'),('cr','Credito')], string='Db/Cr', default='dr')
	partner_id = fields.Many2one('res.partner', string='Empresa')
	# source_id = fields.Many2one('crossovered.source_expenditure', string="Fuente de Financiamiento")
	# process_id = fields.Many2one('crossovered.activity', string="Proceso")
	# budget_account_id = fields.Many2one('account.budget.account', string='Cuenta Presupuesto')
	# fbudget_line_ids = fields.Many2many("account.budget.account", related="account_id.fbudget_line_ids")
	# factivity_ids = fields.Many2many("crossovered.activity", related="account_id.factivity_ids")


	# @api.onchange('account_id')
	# def onchange_account_id_budget(self):
	# 	self.budget_account_id = False
	# 	self.source_id = False
	# 	self.process_id = False
	# 	if self.account_id and self.account_id.account_type == 'expense':
	# 		if len(self.factivity_ids) > 0 and len(self.fbudget_line_ids) > 0:
	# 			domain = [('move_type','=','gasto')]
	# 			self.source_id = self.env.get("crossovered.source_expenditure").search(domain,limit=1).id
	# 		if len(self.factivity_ids) == 1:
	# 			self.process_id = self.factivity_ids.id
	# 		if len(self.fbudget_line_ids) == 1:
	# 			self.budget_account_id = self.fbudget_line_ids.id