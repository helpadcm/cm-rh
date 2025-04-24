# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import requests

class account_journal(models.Model):
	_inherit = 'account.journal'

	equivalence = fields.Integer("Equivalence")
	odoo10_id = fields.Integer(string="Id Odoo 10")

class res_partner(models.Model):
	_inherit = 'res.partner'

	equivalence					= fields.Integer("Equivalence")
	consumer					= fields.Boolean("Final Consumer")
	food						= fields.Boolean("Final")

class account_tax(models.Model):
	_inherit = 'account.tax'

	consumer					= fields.Boolean("Final Consumer")

class account_invoice(models.Model):
	_inherit = 'account.move'

	pk2_id 		= fields.Char(string="Clave PNR-USER")
	partner_name = fields.Char("Nombre de la empresa")
	is_sync = fields.Boolean("Sincronizacion")
	rtn_name = fields.Char("RTN")
	pnr_code = fields.Char(string="PNR")
	origin = fields.Char(string="Referencia/Descripcion")
	
	@api.onchange('partner_id')
	def change_partner(self):
		if not self.is_sync:
			self.partner_name=self.partner_id.name
		else:
			self.partner_name=self.partner_id.name


	def sync_invoices(self):
		last_date = datetime.now().date() - timedelta(days=1)
		url = "http://10.1.4.56:8000/get_invoices?start_date=%s&end_date=%s&limit=%s"%(last_date, last_date,40)
		# url = "http://181.189.230.70/get_invoices?start_date=%s&end_date=%s"%(actual_date, actual_date)
		response = requests.get(url)

		if response.status_code == 200:
			invoices, moves = response.json()
			self.create_invoices(invoices)
			self.create_moves(moves)
	
	def create_invoices(self, invoices):
		for inv in invoices:
			partner_id = self.search_data('res.partner', inv['partner_id'][0])
			user_id = self.search_data('res.users', inv['user_id'][0])
			currency_id = self.env['res.currency'].search([('name', '=', inv['currency_id'][1])], limit=1)

			if partner_id:
				invoice_values = {
					'pnr_code': inv['name'],
					'origin': inv['origin'],
					'internal_number': inv['move_name'],
					'invoice_date': inv['date'],
					'invoice_user_id': user_id,
					'partner_name': inv['partner_name'],
					'rtn_name': inv['rtn_name'],
					'currency_id': currency_id.id,
					'is_sync': inv['is_sync'],
					'partner_id': partner_id if partner_id else False,
					'move_type': inv['type']
				}

				if not inv['move_name']:
					invoice_values.update({'name': 'Borrador'})
				else:
					invoice_values.update({'name': inv['move_name']})

				journal_id = self.env['account.journal'].search([('code','=',inv['journal_id'][0].get('code'))])
				if journal_id:
					invoice_values.update({'journal_id': journal_id.id})

				if inv['payment_term_id']:
					term_id = self.search_data('account.payment.term', inv['payment_term_id'][0])
					if term_id:
						invoice_values.update({'invoice_payment_term_id': term_id})
				
				invoice_id = self.env['account.move'].create(invoice_values)

				for line in inv['invoice_line_ids']:
					product_id = False
					if line['product_id']:
						product_id = self.env['product.product'].search([('name', '=', line['product_id'][1])], limit=1).id

					tax_ids = False
					if line['invoice_line_tax_ids']:
						# id_odoo10 = line['invoice_line_tax_ids'][0]
						tax_ids = self.env['account.tax'].search([('odoo10_id','in',line['invoice_line_tax_ids'])])

					lines_values = {
						'move_id': invoice_id.id,
						'product_id': product_id,
						'name': line['name'],
						'quantity': line['quantity'],
						'price_unit': line['price_unit']
					}

					if line['account_id']:
						account = line['account_id'][1]
						code, name_account = account.split(maxsplit=1)
						account_id = self.env['account.account'].search([('code', '=', code)])
						if account_id:
							lines_values.update({'account_id': account_id.id})

					if tax_ids:
						lines_values.update({'tax_ids': [(6, 0, tax_ids.ids)]})

					self.env['account.move.line'].create(lines_values)

	def create_moves(self, moves):
		for move in moves:
			# user_id = self.search_data('res.users', inv['user_id'][0])
			# currency_id = self.env['res.currency'].search([('name', '=', inv['currency_id'][1])], limit=1)

			move_values = {
				'name': move['name'],
				'internal_number': move['name'],
				'ref': move['ref'],
				'date': move['date'],
				'move_type': 'entry'
			}

			journal_id = self.env['account.journal'].search([('code','=',move['journal_id'][0].get('code'))])
			if journal_id:
				move_values.update({'journal_id': journal_id.id})

			lines = []
			for line in move['line_ids']:
				partner_id = False
				if line['partner_id']:
					partner_id = self.search_data('res.partner', line['partner_id'][0])

				if line['currency_id']:
					currency_id = self.env['res.currency'].search([('name', '=', line['currency_id'][1])], limit=1)
				else:
					currency_id = self.env.user.company_id.currency_id

				lines_values = {
					'partner_id': partner_id if partner_id else False,
					'currency_id': currency_id.id if currency_id else False,
					'name': line['name'],
					'debit': line['debit'],
					'credit': line['credit']
				}

				if line['account_id']:
					account = line['account_id'][1]
					code, name_account = account.split(maxsplit=1)
					account_id = self.env['account.account'].search([('code', '=', code)])
					if account_id:
						lines_values.update({'account_id': account_id.id})
				lines.append((0, 0, lines_values))
					
			move_values.update({'line_ids': lines})
			move_id = self.env['account.move'].create(move_values)

	def search_data(self, model, search_id):
		if search_id:
			return self.env[model].search([('odoo10_id', '=', search_id)], limit=1).id
		return False

class account_invoice_line(models.Model):
	_inherit = 'account.move.line'

	external_tax					= fields.Float("External Tax")
	YQAmount					= fields.Float(string="YQAmount")
	TAAmount					= fields.Float(string="TAAmount")
	YRAmount					= fields.Float(string="YRAmount")
	TDAmount					= fields.Float(string="TDAmount")
	TIAmount					= fields.Float(string="TIAmount")
	YZAmount					= fields.Float(string="YZAmount")
	sub_invoice					= fields.Boolean(string="Appear in Invoice",default=True)
	donate						= fields.Boolean(string="Donate")
	#@api.one
	#@api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
	#'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
	#'invoice_id.date_invoice')
	# def _compute_price2(self):
	# 	res = super(account_invoice_line,self)._compute_price()
	# 	self.price_subtotal += self.external_tax

class account_payment(models.Model):
	_inherit = 'account.payment'

	pk2_id 		= fields.Char(string="Clave PNR-USER")
	is_sync		= fields.Boolean("From Sync")
	user_id				=	fields.Many2one('res.users',string='User',default=lambda self: self.env.user)
	PointOfSaleID				= fields.Many2one('sale.point_of_sale',string="PointOfSale ID")