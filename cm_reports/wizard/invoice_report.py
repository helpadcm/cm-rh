# -*- coding: utf-8 -*-
from odoo import api, fields, models

ARRAY_TYPE=[
('in_invoice', 'Proveedor'),
('out_invoice', 'Cliente'),
]

ARRAY_GROUP=[
('partner', 'Contacto'),
('month', 'Fecha'),
('partner_month','Contacto y fecha'),
('month_partner','Fecha y contacto')
]

class wizard_book(models.TransientModel):
	_name = "cm_reports.invoice_reports"
	_description = "Reportes de facturas"

	date_from = fields.Date(string='Fecha de Inicio')
	date_to = fields.Date(string='Fecha Final')
	partner_ids	= fields.Many2many('res.partner', string="Contactos", domain=['|',('is_supplier','=',True), ('is_customer','=',True)])
	type_of		= fields.Selection(ARRAY_TYPE, string='Tipo')
	show_detail	=fields.Boolean(string="Ver Detalles", default=True)
	group_ledger	= fields.Selection(ARRAY_GROUP, string='Agrupar por')
	company_id = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env.user.company_id.id)
	
	@api.onchange('type_of')
	def change_type(self):
		self.partner_ids = None
		if self.type_of == 'out_invoice':
			return {'domain':{'partner_ids':[('is_customer','=',True)]}}
		if self.type_of == 'in_invoice':
			return {'domain':{'partner_ids':[('is_supplier','=',True)]}}

	def check_report(self):
		data = {}
		data['form'] = self.read(['date_to', 'date_from', 'partner_ids', 'type_of','show_detail','group_ledger','company_id'])[0]
		used_context = self.env.context
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
		if self.env.context.get('export_excel'):
			return self.env.ref('cm_reports.report_invoice_export_general_invoice_xls').report_action(self,data = data)

		return self.env.ref('cm_reports.report_invoice_export_general_invoice').report_action(self, data = data)
	
