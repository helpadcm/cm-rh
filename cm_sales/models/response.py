# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError
ARRAY_sale=[
('draft','Draft'),
('cancel','Cancel'),
('done','Done')

]
ARRAY_calculate=[

('based','Based in Lines'),
('always','Always')

]
class statement_odoo(models.Model):
	_name = 'sale.statement_odoo'
	_description = "Estado de ventas de odoo"
	_inherit = ['mail.thread']

	active 						= fields.Boolean(string="Activo",default=True)
	state 						= fields.Selection(ARRAY_sale,string="State",default="draft",tracking=True)
	SaleStatementID 			= fields.Integer(string="Sale Statement ID")
	SaleStatementDateAndHourLT 	= fields.Datetime(string="Date")
	StatementTypeID				= fields.Many2one('sale.transaction',string="TypeID")
	StatementTypeID2			= fields.Integer(string="TypeID")
	PNRID						= fields.Integer(string="PNR ID")
	PNRCode						= fields.Char(string="PNR CODE")
	RecordStatement				= fields.Char(string="Statement")
	PointOfSaleID				= fields.Many2one('sale.point_of_sale',string="PointOfSale ID")
	PointOfSaleID2				= fields.Integer(string="PointOfSale ID")
	CustomerName				= fields.Char(string="Customer Name")
	PaymentMode					= fields.Char(string="Payment Mode")
	SaleCurrency				= fields.Char(string="Sale Currency")
	BaseCurrencyAmount			= fields.Float(string="Amount")
	BaseCurrencyAmountWithoutTaxes=fields.Float(string="Amount Without Taxes")
	BaseCurrencyTaxAmount		= fields.Float(string="Amount Tax")
	AgentID						= fields.Many2one('sale.agent',string="AgentID")
	AgentID2					= fields.Integer(string="AgentID")
	OriginalTicketNumber		= fields.Char(string="OriginalTicketNumber")
	TicketNumber				= fields.Char(string="TicketNumber")
	CustomerID					= fields.Integer(string="CustomerID")
	partner_id					= fields.Many2one('res.partner',string="Partner")
	TripType					= fields.Char(string="TripType")
	FHAmount					= fields.Float(string="FHAmount")
	HNAmount					= fields.Float(string="HNAmount")
	YQAmount					= fields.Float(string="YQAmount")
	TAAmount					= fields.Float(string="TAAmount")
	YRAmount					= fields.Float(string="YRAmount")
	TDAmount					= fields.Float(string="TDAmount")
	TIAmount					= fields.Float(string="TIAmount")
	YZAmount					= fields.Float(string="YZAmount")
	PassengerType				= fields.Char(string="Type Passenger")
	currency_id 				= fields.Many2one('res.currency',string="Currency")
	invoice						= fields.Boolean(string="INV",default=True)
	error						= fields.Boolean(string="Error",default=False)
	rtn 						= fields.Char(string="RTN")
	name						= fields.Char(string="Name Invoice")
	company_id					= fields.Many2one('res.company',string="Company")
	value 						= fields.Float('Value')
	find_value					= fields.Boolean("Find Value")
	diff_value					= fields.Float("Diff")
	is_diff						= fields.Boolean("is Iff")



	def do_minus(self):
		self.invoice=not self.invoice
		
	def do_cancel(self):
		ids= self.env.context.get('active_ids',[self.env.context.get('active_id')])
		for record in self.browse(ids):
			if record.state=='draft':
				record.state='cancel'
				
	def show_details(self):
		view_id = self.env.ref('cm_sales.statement_odoo_form_view').id
		return {
		'name': _('Details'),
		'type': 'ir.actions.act_window',
		'view_type': 'form',
		'view_mode': 'form',
		'res_model': 'sale.statement_odoo',
		'views': [(view_id, 'form')],
		'view_id': view_id,
		'target':  self.env.context.get('target','new'),
		'res_id': self.ids[0],
		'context': self.env.context}

class statement_odoo(models.Model):
	_name = 'sale.cashstatement_odoo'
	_description = "Estado de efectivo en ventas"

	active 						= fields.Boolean(string="Activo",default=True)
	state 						= fields.Selection(ARRAY_sale,string="State",default="draft")
	CashStatementID 			= fields.Char(string="Sale CashStatement ID")
	CashStatementDateAndHourLT 	= fields.Datetime(string="Date")
	PNRID						= fields.Integer(string="PNR ID")
	PNRCode						= fields.Char(string="PNR CODE")
	RecordStatement				= fields.Char(string="Statement")
	PointOfSaleID				= fields.Many2one('sale.point_of_sale',string="PointOfSale ID")
	PointOfSaleID2				= fields.Integer(string="PointOfSale ID")
	AgentID						= fields.Many2one('sale.agent',string="AgentID")
	AgentID2					= fields.Integer(string="AgentID")
	FormOfPaymentID				= fields.Many2one('account.journal',string="FormOfPaymentID")
	FormOfPaymentID2			= fields.Integer(string="FormOfPaymentID")
	BaseCurrency				= fields.Char(string="Cash Currency")
	RecordReferenceNumber		= fields.Char(string="Ref")
	BaseCurrencyAmount			= fields.Float(string="Amount")
	residual					= fields.Float(string="Residual")
	CustomerID					= fields.Integer(string="CustomerID")
	partner_id					= fields.Many2one('res.partner',string="Partner")
	currency_id 				= fields.Many2one('res.currency',string="Currency")
	invoice						= fields.Boolean(string="INV",default=True)
	error						= fields.Boolean(string="Error",default=False)
	company_id					= fields.Many2one('res.company',string="Company")
	
	
	def do_minus(self):
		self.invoice=not self.invoice
		
	def show_details(self):
		view_id = self.env.ref('cm_sales.cashstatement_odoo_form_view').id
		return {
		'name': _('Details'),
		'type': 'ir.actions.act_window',
		'view_type': 'form',
		'view_mode': 'form',
		'res_model': 'sale.cashstatement_odoo',
		'views': [(view_id, 'form')],
		'view_id': view_id,
		'target': 'new',
		'res_id': self.ids[0],
		'context': self.env.context}


class transaction(models.Model):
	_name = 'sale.transaction'
	_description = "Transacciones en ventas"
	_inherit = ['mail.thread']

	name						= fields.Char(string="Name",tracking=True)
	equivalence					= fields.Integer("Equivalence",tracking=True)
	calculate					= fields.Boolean("Calculate Tax",default=True)
	external_tax				= fields.Boolean("External Tax",default=False)
	dcalculate					= fields.Selection(ARRAY_calculate,string="Calculate Tax",tracking=True)
	transaction_ids				= fields.One2many('sale.transaction_lines','transaction_id',string="Transactions")
	label						= fields.Char(string="Etiqueta")
	ulabel						= fields.Boolean(string="Using Label")
	donate						= fields.Boolean(string="Otros")
	find_value					= fields.Boolean(string="Find Value")

class transaction_lines(models.Model):
	_name = 'sale.transaction_lines'
	_description = "Lines de transaccion"

	transaction_id				= fields.Many2one('sale.transaction',string="Transaction")
	account_id					= fields.Many2one('account.account',string="Account")
	company_id					= fields.Many2one('res.company',string="Company")

class agent(models.Model):
	_name = 'sale.agent'
	_description = "Agentes de venta"

	name						= fields.Char(string="Name")
	lname						= fields.Char(string="LastName")
	equivalence					= fields.Integer("Equivalence")
	user_id						= fields.Many2one('res.users',string="User")

class point_sale(models.Model):
	_name = 'sale.point_of_sale'
	_description = "Punto de Venta Web"
	_inherit = ['mail.thread']

	name						= fields.Char(string="Name",tracking=True)
	analytic_id					= fields.Many2one('account.analytic.account')#analytic.group_analytic_accounting
	equivalence					= fields.Integer("Equivalence",tracking=True)
	company_id					= fields.Many2one('res.company',string="Company",tracking=True)
	journal_id					= fields.Many2one('account.journal',string="Journal",tracking=True)
