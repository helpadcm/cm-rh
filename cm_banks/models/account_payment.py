# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class res_company(models.Model):
	_inherit = 'res.company'

	ilc_permit	= fields.Float(string="Diferencia Disponible",default=5)

class ap_account_payment(models.Model):
	_inherit='account.payment'

	was_unreconcilied = fields.Boolean(string='Desconciliado')
	deposit_id = fields.Many2one('banks.deposit', string='Deposit Ref')
	analytic_account_id	=	fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	number_doc = fields.Char(string = 'Numero')
	write_off_line = fields.One2many('account.payment.writeoffline','payment_id',string="Write off lines")
	partner_id_for_parents = fields.Many2one('res.partner',string="Partner")
	pay_method_type = fields.Selection([
				('check','Cheque'),
				('transference','Transferencia'),
				('otros','Otros')], string='Tipo de Transaccion')
	total_usd = fields.Float(string="USD")

	@api.onchange('amount', 'date', 'currency_id')
	def _compute_currency_amount(self):
		base_USD = self.env.ref('base.USD')
		for payment in self:
			# Siempre se realiza la conversión a USD, sin importar la divisa de origen
			payment.total_usd = payment.currency_id._convert(
				payment.amount,
				base_USD,
				payment.company_id,
				payment.date
			)

	def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
		res = super(ap_account_payment, self)._prepare_move_line_default_vals(write_off_line_vals=None, force_balance=None)
		for line in res:
			if line.get('account_id') == self.journal_id.default_account_id.id:
				if self.analytic_account_id:
					distribution_line = {str(self.analytic_account_id.id): 100.0}
					line.update({'analytic_distribution': distribution_line})

		total_credit = 0
		total_debit = 0
		total_amount_currency = 0
		for payment in self:
			lines_list = []
			total_writeoff_company = 0.0
			total_writeoff_currency = 0.0
			total_debit = 0
			total_credit = 0
			company_currency = payment.company_id.currency_id
			payment_currency = payment.currency_id
			if payment.write_off_line:
				for line in payment.write_off_line:
					if not line.account_id:
						continue

					amount_currency = line.amount_currency
					# if payment.payment_type == 'outbound':
					# 	amount_currency = -abs(amount_currency)
					# else:
					# 	amount_currency = abs(amount_currency)
					if line.credit != 0:
						amount_currency = -abs(amount_currency)
					if line.debit != 0:
						amount_currency = abs(amount_currency)

					if company_currency.id == payment_currency.id:
						credit = line.credit
						debit = line.debit
					else:
						credit = payment_currency._convert(line.credit, company_currency, payment.company_id, payment.date)
						debit = payment_currency._convert(line.debit, company_currency, payment.company_id, payment.date)

					total_debit += debit
					total_credit += credit

					vals = {
						'name': line.description,
						'date_maturity': payment.date,
						'amount_currency': amount_currency,
						'currency_id': payment.currency_id.id,
						'debit': debit,
						'credit': credit,
						'partner_id': payment.partner_id.id,
						'account_id': line.account_id.id,
					}

					if line.analytic_account_id:
						distribution_line = {str(line.analytic_account_id.id): 100.0}
						vals.update({'analytic_distribution': distribution_line})

					lines_list.append(vals)
					
					total_writeoff_company += debit - credit
					total_writeoff_currency += amount_currency

				for line in res:
					# Nota: destination_account_id es la cuenta CXP/CXC original
					if line.get('account_id') == payment.destination_account_id.id:
						if payment.payment_type == 'outbound':  # Pago a proveedor
							if total_credit > 0:
								line['amount_currency'] += abs(total_writeoff_currency)
								line['debit'] += total_credit
							if total_debit > 0:
								line['amount_currency'] -= abs(total_writeoff_currency)
								line['debit'] -= total_debit

						elif payment.payment_type == 'inbound':  # Pago de cliente
							if total_debit > 0:
								line['amount_currency'] -= abs(total_writeoff_currency)
								line['credit'] += total_debit
							if total_credit > 0:
								line['amount_currency'] += abs(total_writeoff_currency)
								line['credit'] -= total_credit
						break

				res.extend(lines_list)
		return res

	def _synchronize_from_moves(self, changed_fields):
		"""
		Permitir múltiples cuentas por cobrar/pagar cuando el pago tiene write_off_lines personalizados.
		"""
		if self._context.get('skip_account_move_synchronization'):
			return super()._synchronize_from_moves(changed_fields)

		for pay in self.with_context(skip_account_move_synchronization=True):

			if pay.move_id.statement_line_id:
				continue

			move = pay.move_id
			move_vals_to_write = {}
			payment_vals_to_write = {}

			if 'journal_id' in changed_fields and pay.journal_id.type not in ('bank', 'cash'):
				raise UserError(_("A payment must always belongs to a bank or cash journal."))

			if 'line_ids' in changed_fields:
				all_lines = move.line_ids
				liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

				if len(liquidity_lines) != 1:
					raise UserError(_(
						"Journal Entry %s is not valid. In order to proceed, the journal items must "
						"include one and only one outstanding payments/receipts account.",
						move.display_name,
					))

				if len(counterpart_lines) != 1:
					if not (pay.write_off_line):
						raise UserError(_(
							"Journal Entry %s is not valid. In order to proceed, the journal items must "
							"include one and only one receivable/payable account (with an exception of "
							"internal transfers).",
							move.display_name,
						))
					else:
						account_write_ids = set(pay.write_off_line.mapped('account_id').ids)
						account_counterpart_ids = set(counterpart_lines.mapped('account_id').ids)
						counterpart_account_id = list(account_counterpart_ids - account_write_ids)
						counterpart_lines = counterpart_lines.filtered(lambda line: line.account_id.id == counterpart_account_id[0])

				if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
					raise UserError(_(
						"Journal Entry %s is not valid. In order to proceed, the journal items must "
						"share the same currency.",
						move.display_name,
					))

				if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
					raise UserError(_(
						"Journal Entry %s is not valid. In order to proceed, the journal items must "
						"share the same partner.",
						move.display_name,
					))

				if counterpart_lines:
					if counterpart_lines.account_id.account_type == 'asset_receivable':
						partner_type = 'customer'
					else:
						partner_type = 'supplier'

					liquidity_amount = liquidity_lines.amount_currency

					move_vals_to_write.update({
						'currency_id': liquidity_lines.currency_id.id,
						'partner_id': liquidity_lines.partner_id.id,
					})
					payment_vals_to_write.update({
						'amount': abs(liquidity_amount),
						'partner_type': partner_type,
						'currency_id': liquidity_lines.currency_id.id,
						'destination_account_id': counterpart_lines.account_id.id,
						'partner_id': liquidity_lines.partner_id.id,
					})
					if liquidity_amount > 0.0:
						payment_vals_to_write.update({'payment_type': 'inbound'})
					elif liquidity_amount < 0.0:
						payment_vals_to_write.update({'payment_type': 'outbound'})

			move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
			pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if vals.get('partner_id') and not vals.get('partner_id_for_parents'):
				vals.update({'partner_id_for_parents':vals.get('partner_id')})
		records = super().create(vals_list)
		records._compute_currency_amount()
		return records

	def action_post(self):
		res = super(ap_account_payment, self).action_post()
		for rec in self:
			if rec.partner_type in ['supplier','customer']:    
				if rec.move_id.name in ['Borrador','/']:
					sequence_id = rec.journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == rec.pay_method_type)
					if sequence_id:
						rec.name = sequence_id.next_by_id()
					else:
						rec.name = rec.journal_id.sequence_id.next_by_id()
			rec.move_id.internal_number = rec.move_id.name
		return res

	def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
		""" Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
		"""
		return {
			'partner_id': self.partner_id.id or False,
			'move_id': move_id,
			'debit': debit,
			'credit': credit,
			'amount_currency': amount_currency or False,
		}

	def post_multi(self,keep_open = 0,write_off=0,move_ret=False,cant_ret=0,type_invoice='in_invoice'):
		self.env.context = dict(self.env.context or {})
		if self.existen_numeros_repetidos():
			raise UserError(_("Ya hay un documento validado con este numero"))
		else:
			self.env.context.update({'no_update':False})

		#post original
		for rec in self:
			voucher =  rec
			seq_model = self.env.get('ir.sequence')
			old_partner_id = voucher.partner_id.id
			
			# if voucher.partner_id_for_parents.parent_id.id:
			# 	rec.write({'partner_id': voucher.partner_id_for_parents.parent_id.id})		
			
			if voucher.name != 'Draft Payment':
				self.env.context.update({'no_update':True,'from_voucher':True})
			
			if rec.state != 'draft':
				raise UserError(_("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)
			
			# if any(inv.state != 'open' for inv in rec.invoice_ids):
			# 	raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
			
			if rec.partner_type == 'customer':
				if rec.payment_type == 'inbound':
					doc_type = 'deposit'
			if rec.partner_type == 'supplier':
				if rec.payment_type == 'outbound':
					doc_type = rec.pay_method_type
			
			if rec.name == '/':
				name = "/"
				seq_id = False
				if doc_type == 'otros':
					if self.journal_id.sequence_id:
						seq_id = self.journal_id.sequence_id.id
				else:
					if self.journal_id.sequence_ids:
						seq_id = self.journal_id.sequence_ids.filtered(lambda line: line.code2.code == doc_type)
				
				if not seq_id:
					raise UserError(_('Por favor active la secuencia para el diario seleccionado!'))

				if self.journal_id.sequence_id:
					if not self.journal_id.sequence_id.active:
						raise UserError(_('Por favor active la secuencia para el diario seleccionado!'))
					rec.name = seq_id.next_by_id()
				else:
					rec.name= None

			# Create the journal entry
			amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
			if move_ret:
				move = move_ret
			else:
				move = self.env['account.move'].create(self.with_context({'sequence':rec.name})._get_move_vals())
			
			
			aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)

			invoice_currency = False
			# if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
			# 	invoice_currency = self.invoice_ids[0].currency_id
			
			debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
			
			if not self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
				amount_currency = -amount_currency
			
			if not self.currency_id != self.company_id.currency_id:
				amount_currency = 0
			
			if credit>0:
				amount_currency=-amount_currency

			liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
			#cuenta analytica para diario
			liquidity_aml_dict.update({'analytic_account_id':self.analytic_account_id.id})
			#----------------------------
			liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
			liquidity_aml_dict['amount_currency'] = -amount_currency
			aml_obj.create(liquidity_aml_dict)
			rc_rest = {}
			for rc_line in rec.lines_cr:
				rc_rest[rc_line.id] = rc_line.amount
			for line in rec.payment_line_ids:
				contrc = 0
				for rc_line in rec.lines_cr:
					if contrc < line.amount and rc_rest[rc_line.id]>0:
						temp = rc_line.move_line_id.amount_residual 
						if (line.amount - contrc) < rc_rest[rc_line.id]:
							value = abs(line.amount - contrc)
						else:
							value = rc_rest[rc_line.id]
						rc_line.move_line_id.write({'amount_residual':value})
						line.move_line_id.invoice_id.assign_outstanding_credit([rc_line.move_line_id.id])
						contrc += value
						rc_rest[rc_line.id] -= value

						rc_line.move_line_id.write({'amount_residual':temp-value})
				if contrc < line.amount:
					if (line.amount - contrc) > 0:
						value = abs(line.amount - contrc)
						rec._create_payment_entry_multi(value,move,line.move_line_id.invoice_id.id,line,cant_ret)

						contrc += value
				
			debit = 0
			credit = keep_open
			if type_invoice == 'out_invoice':
				debit = keep_open
				credit = 0
			if write_off>0:
				for wo_line in rec.write_off_line:
					val = 0
					if wo_line.credit > 0:
						val += wo_line.credit
					else:
						val -= wo_line.debit
					writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
					debit,credit,amount_currency_wo,currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(-val, self.currency_id, self.company_id.currency_id, False)
					
					writeoff_line['debit'] = debit
					writeoff_line['credit'] = credit
					writeoff_line['analytic_account_id'] = wo_line.analytic_account_id.id
					#writeoff_line['chqmanalitics'] = wo_line.chqmanalitics.id
					#writeoff_line['analytic_tag_ids'] = [(6,0,wo_line.analytic_tag_ids.ids)]
					#if type_invoice == 'in_invoice':
					#	amount_currency_wo = -amount_currency_wo
					#	writeoff_line['debit'] = credit
					#	writeoff_line['credit'] = debit
					writeoff_line['name'] = _(wo_line.description)
					writeoff_line['account_id'] = wo_line.account_id.id
					writeoff_line['partner_id'] = wo_line.partner_id.id
					writeoff_line['amount_currency'] = amount_currency_wo
					writeoff_line['currency_id'] = currency_id
					writeoff_line = aml_obj.create(writeoff_line)

					liquidity_aml_dict = self._get_shared_move_line_vals(credit,debit, -amount_currency_wo, move.id, False)
									
					liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-val))
				
								#aml_obj.create(liquidity_aml_dict)
			if round(keep_open,2) > 0:
				debit,credit,amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(-keep_open, self.currency_id, self.company_id.currency_id, False)
				
				counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency_wo, move.id, False)
				counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
				counterpart_aml_dict.update({'currency_id': currency_id})
				counterpart_aml = aml_obj.create(counterpart_aml_dict)
				liquidity_aml_dict = self._get_shared_move_line_vals(credit,debit, -amount_currency_wo, move.id, False)
				liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-keep_open))
			if rec.payment_type == 'transfer':
				transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
				transfer_debit_aml = rec._create_transfer_entry(amount)
				
				(transfer_credit_aml + transfer_debit_aml).reconcile()
			rec.write({'state': 'posted', 'move_name': move.name,'was_unreconcilied':True})
		#agregatte
		self.update_state_draf()#added line
		self.write({
		        'number_doc': voucher.name,
				'move_id':move.id,'partner_id': old_partner_id
		    })
		move.post()
		#farrl
		return move

	def existen_numeros_repetidos(self):
		for voucher in self:
			doc_type = ""
			if not voucher.was_unreconcilied:
				doc_type = voucher.pay_method_type
				if not doc_type:
					doc_type = 'deposit'
				number = False
				voucher.number_doc = voucher.with_context({'return':False}).next_seq_number(voucher.journal_id, doc_type)
				if voucher.number_doc:
					number = voucher.number_doc
			else:
				number = voucher.name

			res = self.env['account.payment'].search(['&','|','&',('state','!=','draft'),('name','=',number),'&',('state','=','draft'),'&',('name','=',number),('was_unreconcilied','=',True),('id','!=',voucher.id)])
			if doc_type == 'deposit':
				res2 = 	self.env['banks.deposit'].search(['|','&',('state','!=','draft'),('number','=',number),'&',('state','=','draft'),'&',('number','=',number),('was_unreconcilied','=',True)])	
			else:			
				res2 = 	self.env['mcheck.mcheck'].search(['|','&',('state','!=','draft'),('number','=',number),'&',('state','=','draft'),'&',('number','=',number),('was_unreconcilied','=',True)])	
			if res or res2:
				number = voucher.with_context({'return':True}).next_seq_number(voucher.journal_id, doc_type)
				return self.with_context({'number':number}).existen_numeros_repetidos()
			voucher.number_doc = number
		return False

	def next_seq_number(self, journalid, doc_type, context=None):
		self.env.context = dict(self.env.context or {})
		if journalid:
			if doc_type == 'otros':
				if journalid.sequence_id:
					self.env.context.update({'no_update' : True})
					name = journalid.sequence_id.next_by_id()
					return name
				else:
					raise osv.except_osv(_('Por favor active la secuencia para el diario seleccionado!'))
			
			if self.partner_type == 'customer': 
				doc_type ='deposit' 
			else: 
				doc_type = doc_type  
		else: 
			return None

		if not journalid == False and doc_type != False:
			if journalid.sequence_ids:
				seq_id = journalid.sequence_ids.filtered(lambda line: line.code2.code == doc_type)
				if not seq_id:
					raise osv.except_osv(_('Por favor configure una secuencia del tipo de documento %s en el diario %s!'%(doc_type, journalid.name)))
			else:
				raise osv.except_osv(_('Por favor configure una secuencia del tipo de documento %s en el diario %s!'%(doc_type, journalid.name)))
			
			if journalid.sequence_id:
				if not journalid.sequence_id.active:
					raise osv.except_osv(_('Por favor active la secuencia para el diario seleccionado!'))
				
				if self.env.context.get('return'):
					self.env.context.update({'no_update' : False})
				else:
					self.env.context.update({'no_update' : True})
				
				name = seq_id.next_by_id()
				return  name
			else:
				return None
		else:
			return None

	def _get_move_vals(self, journal=None):
		""" Return dict to create the payment move
		"""
		seq_obj = self.env['ir.sequence']
		journal = journal or self.journal_id
		if not journal.sequence_id:
			raise UserError(_('Error de Configuracion!'), _('El diario %s no tiene secuencia, por favor especifique una.') % journal.name)
		if not journal.sequence_id.active:
			raise UserError(_('Error de Configuracion!'), _('La secuencia del diario %s esta desactivada.') % journal.name)
		if self._context.get('sequence',False):
			name = self.name or self.env.context['sequence']
		else:
			name = self.name or journal.with_context(ir_sequence_date=self.date).sequence_id.next_by_id()
		return {
			'name': name,
			'date': self.date,
			'ref': self.ref or '',
			'company_id': self.company_id.id,
			'journal_id': journal.id,
		}

	def add_analytic_account(self):
		if self.move_id and self.journal_id.code == 'EFU':
			for line in self.move_id.line_ids:
				if line.debit > 0:
					analytic_account_id = self.env['account.analytic.account'].search([('partner_id','=',self.user_id.partner_id.id)])
					if analytic_account_id:
						distribution_line = {str(analytic_account_id.id): 100.0}
						line.analytic_distribution = distribution_line

class write_off_line(models.Model):
	_name = "account.payment.writeoffline"
	_description = "Distribucion de pagos"

	account_id = fields.Many2one('account.account',string="Account",required=True)
	description = fields.Char(string="Description")
	debit = fields.Float(string="Debit")
	credit = fields.Float(string="Credit")
	amount_currency=fields.Float(string="Credit")
	currency_id = fields.Many2one('res.currency',string='Currency')
	payment_id = fields.Many2one('account.payment',string="Payment")
	partner_id	= fields.Many2one('res.partner',string="Partner")
	analytic_account_id = fields.Many2one('account.analytic.account',string="Analytic Account")

class account_payment_line(models.Model):
	_name = "account.payment.line"
	_description = "Lineas de pago"

	move_line_id = fields.Many2one('account.move.line',string="Move lines",required=True)
	account_id = fields.Many2one('account.account',string="Account",required=True)
	date_original = fields.Date(string='Date')
	date_due = fields.Date(string='Date due')
	amount_original = fields.Monetary(currency_field='currency_id',string="Amount original")
	amount_unreconcilied = fields.Monetary(currency_field='currency_id',string="Amount unreconcilied")
	reconcile = fields.Boolean(string="Concilied full")
	amount = fields.Monetary(currency_field='currency_id',string="amount")
	payment_id = fields.Many2one('account.payment',string="Payment",ondelete="cascade")
	currency_id = fields.Many2one('res.currency',string='Currency')
	move_name = fields.Char(string='Move name')
	chqmanalitics=fields.Many2one("account.analytic.account",string="Check Misc Analiticos")

	# @api.onchange('move_line_id','amount_original','amount_unreconcilied')
	# def _onchange_move(self):
	# 	if self.move_line_id:
	# 		self.account_id = self.move_line_id.account_id.id
	# 		self.amount_original=self.move_line_id.invoice_id.amount_total
	# 		self.date_original=self.move_line_id.date
	# 		self.date_due=self.move_line_id.invoice_id.date_due
	# 		self.amount_unreconcilied=self.move_line_id.invoice_id.residual

	# @api.onchange('reconcile')
	# def _onchange_reconcile(self):
	# 	if self.reconcile:
	# 		self.amount = self.amount_unreconcilied

	# @api.onchange('amount')
	# def _onchange_amount(self):
	# 	if self.amount == self.amount_unreconcilied:
	# 		self.reconcile = True
	# 	else:
	# 		self.reconcile = False
