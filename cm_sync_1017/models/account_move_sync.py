# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api
from datetime import datetime, timedelta

class accountMoveSync(models.Model):
    _inherit = 'account.move'

    odoo10_id = fields.Integer(string="Id Odoo 10")

    def sync_invoices(self, invoice_type):
        last_date = datetime.now().date() - timedelta(days=1)
        url = "http://10.1.4.56:8000/get_invoices?start_date=%s&end_date=%s&invoice_type=%s&limit=%s"%(last_date, last_date, invoice_type, 10)
        # url = "http://181.189.230.70/get_invoices?start_date=%s&end_date=%s&invoice_type=%s&limit=%s"%(last_date, last_date, invoice_type, 10)
        response = requests.get(url)

        if response.status_code == 200:
            invoices = response.json()
            for inv in invoices:
                exist = self.exist_number(inv['move_name'], inv['id'])
                if not exist:
                    partner_id = self.search_data('res.partner', inv['partner_id'][0])
                    if partner_id:
                        user_id = self.search_data('res.users', inv['user_id'][0])
                        currency_id = self.env['res.currency'].search([('name', '=', inv['currency_id'][1])], limit=1)
                        print (inv)
                        invoice_values = {
                            'odoo10_id': inv['id'],
                            'payment_reference': inv['name'],
                            'invoice_date': inv['date'],
                            'invoice_user_id': user_id,
                            # 'partner_name': inv['partner_name'],
                            # 'rtn_name': inv['rtn_name'],
                            'currency_id': currency_id.id,
                            # 'is_sync': inv['is_sync'],
                            'partner_id': partner_id if partner_id else False,
                            'move_type': inv['type']
                        }
                        if invoice_type == 'supplier':
                            invoice_values.update({'ref': inv['reference']})
                            if inv['cai_id']:
                                cai_id = self.env['management.cai'].search([('name','=',inv['cai_id'][1])])
                                if cai_id:
                                    invoice_values.update({'cai_id': cai_id.id})


                        if not inv['move_name']:
                            invoice_values.update({'name': 'Borrador'})
                            invoice_values.update({'internal_number': 'Borrador'})
                        else:
                            invoice_values.update({'name': inv['move_name']})
                            invoice_values.update({'internal_number': inv['move_name']})

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

                        if inv['state'] == 'open':
                            invoice_id.action_post()
                        elif inv['state'] == 'paid':
                            invoice_id.action_post()
                            if inv['payment_ids']:
                                self.register_paymet(invoice_id, inv['payment_ids'])

    def search_data(self, model, search_id):
        if search_id:
            return self.env[model].search([('odoo10_id', '=', search_id)], limit=1).id
        return False

    def exist_number(self, number, id_inv):
        move_id = self.search(['|',('name','=',number),('odoo10_id','=',id_inv)])
        if move_id:
            return True
        else:
            return False

    def register_paymet(self, inv_id, payments):
        for pay in payments:
            journal_id = self.env['account.journal'].search([('code','=',pay['journal_id'][0].get('code'))])
            if journal_id.currency_id:
                currency_id = journal_id.currency_id
            else:
                currency_id = self.env.user.company_id.currency_id

            values = {
                'amount': pay['amount'],
                'payment_date': pay['payment_date'],
                'journal_id': journal_id.id,
                'currency_id': currency_id.id,
                'communication': pay['communication'],
                'payment_type': 'outbound',  # el dinero sale de tu empresa
                'partner_type': 'supplier',
            }
            if pay['apply_retentions']:
                print ("////////////////////// apply retentions //////////////////////")
            else:
                if inv_id.state == 'posted':
                    reconcilable_lines = inv_id.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled and l.balance != 0)

                    line_id_to_reconcile = reconcilable_lines[0].id if reconcilable_lines else False

                    values.update({'line_ids': [(6, 0, reconcilable_lines.ids)]})
                    payment_register_wizard = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=[line_id_to_reconcile]).create(values)

                    payment_register_wizard.action_create_payments()