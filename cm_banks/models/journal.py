# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime
import locale
import pytz

class banks_account_journal(models.Model):
	_inherit = 'account.journal'

	require_analytic_account = fields.Boolean(string="Requiere Cuenta Analitica")
	analytic_account_ids = fields.Many2many('account.analytic.account')
	checkmiscelaneous= fields.Boolean(string="Cheques Miscelaneos",default=False)
	allow_creditdebit= fields.Boolean(string="Permitir debitos y creditos",default=False)
	allow_multi_sequence= fields.Boolean(string="Permitir Multi-secuencias",default=False)
	allow_banks_transferences= fields.Boolean(string="Permitir transacciones bancarias",default=False)
	sequence_ids= fields.Many2many('ir.sequence',string='Secuencias')
	commission_account= fields.Many2one('account.account',string='Cuenta para comision')	
	comnsolidate_deposit= fields.Boolean(string="Depositos Conciliados")
	city = fields.Char(string="Ciudad")

	def create_secuences_if_dont_exits(self,allow_multi_sequence,sequence_ids):
		res={}
		value = {}
		sequences = []
		actual_codes=[]
		sequences_added = self.env['ir.sequence'].browse(sequence_ids)

		if allow_multi_sequence:
			for sec in sequences_added:
				if sec.code2:
					actual_codes.append(sec.code2.name)

			resultado = []
			if 'check' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_ch').id
				if self.env["ir.sequence.type"].search([('code','=','check')]):
					resultado.append({'code':'check','code2':record_id,'name':'CHEQUES','prefix':'CH-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'other' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_other').id
				if self.env["ir.sequence.type"].search([('code','=','other')]):
					resultado.append({'code':'other','code2':record_id,'name':'OTHER','prefix':'OTH-#','padding':8,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'check_cancel' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_ch_c').id
				if self.env["ir.sequence.type"].search([('code','=','check_cancel')]):
					resultado.append({'code':'check_cancel','code2':record_id,'name':'CHEQUES CANCELACION','prefix':'CH-NULL-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'deposit' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_dep').id
				if self.env["ir.sequence.type"].search([('code','=','deposit')]):
					resultado.append({'code':'deposit','code2':record_id,'name':'DEPOSITOS','prefix':'DEP-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'credit' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_cre').id
				if self.env["ir.sequence.type"].search([('code','=','credit')]):
					resultado.append({'code':'credit','code2':record_id,'name':'CREDITOS','prefix':'CRD-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'debit' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_deb').id
				if self.env["ir.sequence.type"].search([('code','=','debit')]):
					resultado.append({'code':'debit','code2':record_id,'name':'DEBITOS','prefix':'DEB-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'banks_transferences' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_dep_bank_transfer').id
				if self.env["ir.sequence.type"].search([('code','=','banks_transferences')]):
					resultado.append({'code':'banks_transferences','code2':record_id,'name':'TRANSFERENCIAS BANCARIAS','prefix':'TRANS-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			if 'transference_cancel' not in actual_codes:
				record_id = self.env.ref('cm_banks.codes_for_ir_sequence_type_tr_c').id
				if self.env["ir.sequence.type"].search([('code','=','transference_cancel')]):
					resultado.append({'code':'transference_cancel','code2':record_id,'name':'TRANSFERENCIAS CANCELACION','prefix':'TRANS-NULL-#','padding':5,'number_next_actual':1,'number_increment':1,'implementation':'no_gap'})
			for s in resultado:
				new_id = self.env['ir.sequence'].create(s)
				sequences.append(new_id.id)
			return sequences				
		else:	
			return sequences
			
	def existe_repeat(self,sequence_ids_list):
		if sequence_ids_list:
			cont=0
			ir_seq_pool = self.env['ir.sequence']
			sequence_ids = ir_seq_pool.browse(sequence_ids_list.ids)
			for seqs in sequence_ids:
				for seqs2 in sequence_ids:
					if seqs.code not in [None,False] and seqs2.code not in [None,False]:
						if not (seqs == seqs2):
							if seqs.code2.name == seqs2.code2.name:
								cont+=1
								if cont>0:
									cont=0
									return seqs.code2.name
				cont=0
			return False
		else:
			return False
					
	def write(self,vals):
		vals = dict(vals or {})
		bandera=True
		ir_seq_pool = self.env['ir.sequence']

		sequence_ids = self.sequence_ids
		if vals.get('sequence_ids'):
			seq_ops = vals['sequence_ids']
			for op in seq_ops:
				if isinstance(op, (list, tuple)) and len(op) == 3 and op[0] in (6,):
					sequence_ids = ir_seq_pool.browse(op[2])
				elif isinstance(op, (list, tuple)) and len(op) == 3 and op[0] in (0,):
					sequence_ids = ir_seq_pool.browse([])
			
			if sequence_ids:
				res = self.existe_repeat(sequence_ids)
				if not res:
					return super(banks_account_journal, self).write(vals)
				else:
					raise osv.except_osv(_('Error!'),_("There is more than one sequence with the code '"+res+"', you have to delete or change one") )	
			else:
				return super(banks_account_journal, self).write(vals)		
		else:
			return super(banks_account_journal, self).write(vals)


	@api.model_create_multi
	def create(self, values):
		sequence_ids=[]
		ir_seq_pool = self.env['ir.sequence']
		for vals in values:
			if vals.get('allow_multi_sequence') and vals.get('type','') == 'bank':
				if len(vals.get('sequence_ids'))>0:
					if len(vals.get('sequence_ids')[0])>=3:
						sequence_ids=vals.get('sequence_ids')[0]
				added_ids = self.create_secuences_if_dont_exits(vals.get('allow_multi_sequence'),sequence_ids)
				vals.update({'sequence_ids':[[6,False, added_ids+sequence_ids]]})
				b = super(banks_account_journal, self).create(vals)
				if b:
					seq_ops = vals['sequence_ids']
					sequence_ids = False
					for op in seq_ops:
						if isinstance(op, (list, tuple)) and len(op) == 3 and op[0] in (6,):
							sequence_ids = ir_seq_pool.browse(op[2])
						elif isinstance(op, (list, tuple)) and len(op) == 3 and op[0] in (0,):
							sequence_ids = ir_seq_pool.browse([])
					if sequence_ids:
						res=self.existe_repeat(sequence_ids)
						if res:
							raise osv.except_osv(_("There is more than one sequence with the code '"+res+"', you have to delete or change one") )
					return b
				else:
					return False
			else:
				return super(banks_account_journal, self).create(values)

	@api.returns('self', lambda value: value.id)
	def copy(self,default=None):
		default = dict(self.env.context or {})
		journal = self
		default.update(
			code=_("%s (copy)") % (journal.code ),  
		        name=_("%s (copy)") % (journal.name )),
		        #allow_multi_sequence=False
		default['allow_multi_sequence']=False
		default['checkmiscelaneous']=False
		default['allow_check_writing']=False
		default['allow_banks_transferences']=False
		default['allow_multi_sequence']=False
		return super(banks_account_journal, self).copy(default)

		

