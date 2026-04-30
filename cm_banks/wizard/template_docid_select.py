# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class anullation_date_wizard(models.TransientModel):
	_name = 'template_docid_select'
	_description = 'Seleccionar Documento en Plantilla'
	
	def Select_Doc(self):
		context = self.env.context
		if context.get('active_id'):
			for selected_doc in self:
				if selected_doc.to_mcheck and selected_doc.doc_id_mcheck:
					valores = {'doc_id': selected_doc.doc_id_mcheck, 'doc_type' :selected_doc.doc_id_mcheck.doc_type }
				elif selected_doc.to_debit_credit and selected_doc.doc_id_debit_credit:
					valores = {'doc_id': selected_doc.doc_id_debit_credit, 'doc_type' : selected_doc.doc_id_debit_credit.doc_type }
				else:
					raise osv.except_osv(_('Error de configuracion !'),_("Intente de nuevo por favor"))

			self.env['banks.template'].browse(context.get('active_id')).write(valores)
		else:
			raise osv.except_osv(_('Error!'),_("La operacion no finalizo, Intente de nuevo!"))

	to_mcheck = fields.Boolean(string='Cheque Miscelaneo o Transferencia', help="Usar como plantilla de Pago Miscelaneo o transferencia", required=False )
	to_debit_credit = fields.Boolean(string='Debito o Credito', help="Usar como plantilla de debito o credito", required=False)
	doc_id_mcheck = fields.Many2one('mcheck.mcheck', string='Documento', help="Documento a usar como plantilla",required=False )
	doc_id_debit_credit = fields.Many2one('debit.credit', string='Documento Debido/Credito', help="Documento a usar como plantilla",required=False )



