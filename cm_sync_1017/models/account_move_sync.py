# -*- coding: utf-8 -*-

import requests
import logging
from odoo import models, fields, api
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class accountMoveSync(models.Model):
    _inherit = 'account.move'

    odoo10_id = fields.Integer(string="Id Odoo 10")

    def sync_invoices(self, invoice_type, limit=1000, opt='production'):
        default_partner_id = self.env['res.partner'].sudo().search([('default_client', '=', True)])
        last_date = datetime.now().date() - timedelta(days=1)
        if self.env.context.get('start_date'):
            last_date = self.env.context.get('start_date')

        if self.env.context.get('opt'):
            opt = self.env.context.get('opt')

        if self.env.context.get('type'):
            invoice_type = self.env.context.get('type')

        if self.env.context.get('limit'):
            limit = self.env.context.get('limit')

        ##################    URL INVOICES COUNT ##########################################
        ip = '181.189.230.70'
        if opt == 'test':
            ip = '10.1.4.56'

        url_inv_count = "http://%s:8000/get_invoices_count?start_date=%s&end_date=%s&invoice_type=%s"%(ip, last_date, last_date, invoice_type)
        response = requests.get(url_inv_count, timeout=60)
        _logger.info(f"Solicitando conteo de facturas de tipo '{invoice_type}' a: {url_inv_count}")
        
        count_response = requests.get(url_inv_count, timeout=60)
        total_items = count_response.json().get("total_invoices", 0)
        _logger.info(f"Cantidad de Facturas tipo '{invoice_type}' es '{total_items}'.")

        offset = 0
        while offset < total_items:
            ##################    URL INVOICES  ##########################################
            _logger.info(f"Solicitando tanda de facturas '{invoice_type}': skip={offset}, limit={limit}")
            url = "http://%s:8000/get_invoices?start_date=%s&end_date=%s&invoice_type=%s&skip=%s&limit=%s"%(ip, last_date, last_date, invoice_type, offset, limit)
            response = requests.get(url, timeout=300)
            if response.status_code == 200:
                invoices = response.json()
                if not invoices:
                    _logger.warning(f"No se recibieron más facturas en la tanda actual para '{invoice_type}'. Posible desincronización o fin de datos. skip={offset}, limit={limit_per_batch}")
                    break

                _logger.info(f"Recibidas {len(invoices)} facturas de tipo '{invoice_type}' en esta tanda. Procesando...")

                odoo10_partner_ids = set()
                odoo10_user_ids = set()
                currency_names = set()
                journal_codes = set()
                odoo10_cai_names = set()
                odoo10_payment_term_ids = set()
                for inv in invoices:
                    if inv.get('partner_id') and isinstance(inv['partner_id'], list) and inv['partner_id'][0]:
                        odoo10_partner_ids.add(inv['partner_id'][0])
                    if inv.get('user_id') and inv['user_id'][0]:
                        odoo10_user_ids.add(inv['user_id'][0])
                    if inv.get('currency_id') and inv['currency_id'][1]:
                        currency_names.add(inv['currency_id'][1])
                    if inv.get('journal_id') and inv['journal_id'].get('code'):
                        journal_codes.add(inv['journal_id']['code'])
                    if invoice_type == 'supplier' and inv.get('cai_id') and inv['cai_id'][1]:
                        odoo10_cai_names.add(inv['cai_id'][1])
                    if inv.get('payment_term_id') and inv['payment_term_id'][0]:
                        odoo10_payment_term_ids.add(inv['payment_term_id'][0])

                partner_map = {}
                if odoo10_partner_ids:
                    partners = self.env['res.partner'].sudo().search([('odoo10_id', 'in', list(odoo10_partner_ids))])
                    partner_map = {p.odoo10_id: p.id for p in partners}


                user_map = {}
                if odoo10_user_ids:
                    users = self.env['res.users'].sudo().search([('odoo10_id', 'in', list(odoo10_user_ids))])
                    user_map = {u.odoo10_id: u.id for u in users}

                currency_map = {}
                if currency_names:
                    currencies = self.env['res.currency'].sudo().search([('name', 'in', list(currency_names))])
                    currency_map = {c.name: c.id for c in currencies}

                journal_map = {}
                if journal_codes:
                    journals = self.env['account.journal'].sudo().search([('code', 'in', list(journal_codes))])
                    journal_map = {j.code: j.id for j in journals}
                
                cai_map = {}
                if odoo10_cai_names:
                    cais = self.env['management.cai'].sudo().search([('name', 'in', list(odoo10_cai_names))])
                    cai_map = {c.name: c.id for c in cais}

                payment_term_map = {}
                if odoo10_payment_term_ids:
                    terms = self.env['account.payment.term'].sudo().search([('odoo10_id', 'in', list(odoo10_payment_term_ids))])
                    payment_term_map = {t.odoo10_id: t.id for t in terms}
                
                for inv in invoices:
                    invoice_date = False
                    if inv.get('date'):
                        try:
                            invoice_date = datetime.strptime(inv['date'], "%Y-%m-%d").date()
                        except ValueError:
                            _logger.warning(f"Formato de 'date' inválido para factura {inv.get('id')}: {inv['date']}")

                    # Resolver IDs de Odoo 17 usando los mapas pre-cargados
                    partner_id = partner_map.get(inv['partner_id'][0]) if inv.get('partner_id') else False
                    user_id = user_map.get(inv['user_id'][0]) if inv.get('user_id') else False
                    currency_id = currency_map.get(inv['currency_id'][1]) if inv.get('currency_id') else False
                    journal_id = journal_map.get(inv['journal_id'].get('code')) if inv.get('journal_id') else False
                    cai_id = cai_map.get(inv['cai_id'][1]) if invoice_type == 'supplier' and inv.get('cai_id') else False
                    payment_term_id = payment_term_map.get(inv['payment_term_id'][0]) if inv.get('payment_term_id') else False

                    # Validaciones antes de crear/actualizar
                    if not partner_id:
                        _logger.warning(f"Partner con ID de Odoo 10 '{inv['partner_id'][0]}' (nombre: {inv['partner_id'][1]}) no encontrado/mapeado en Odoo 17 para factura {inv.get('id')}. Usando Cliente por defecto.")
                        partner_id = default_partner_id.id
                    if not journal_id:
                        _logger.warning(f"Journal con código '{inv['journal_id'].get('code')}' no encontrado/mapeado en Odoo 17 para factura {inv.get('id')}. Saltando esta factura.")
                        continue
                    if not currency_id:
                        _logger.warning(f"Currency con nombre '{inv['currency_id'][1]}' no encontrado/mapeado en Odoo 17 para factura {inv.get('id')}. Saltando esta factura.")
                        continue

                    exist_invoice = self.exist_number(inv['move_name'], inv['id']) 
                    if not exist_invoice:
                        invoice_values = {
                            'odoo10_id': inv['id'],
                            'payment_reference': inv.get('name'),
                            'invoice_date': invoice_date,
                            'invoice_user_id': user_id,
                            'currency_id': currency_id,
                            'partner_id': partner_id,
                            'move_type': inv['type'],
                            'journal_id': journal_id,
                            'state': 'draft',
                            'name': inv.get('move_name') if inv.get('move_name') else 'Borrador',
                            'internal_number': inv.get('move_name') if inv.get('move_name') else 'Borrador',
                            'amount_total': inv.get('amount_total', 0.0)
                        }

                        if invoice_type == 'supplier':
                            invoice_values.update({'ref': inv.get('reference')})
                            if cai_id:
                                invoice_values.update({'cai_id': cai_id})

                        if payment_term_id:
                            invoice_values.update({'invoice_payment_term_id': payment_term_id})

                        _logger.info(f"Creando nueva factura en Odoo 17: ID Externo {inv['id']}")
                        invoice_id = self.env['account.move'].sudo().create(invoice_values)
                        for line in inv['invoice_line_ids']:
                            product_id = False
                            if line['product_id']:
                                product_id = self.env['product.product'].search([('name', '=', line['product_id'][1])], limit=1).id

                            tax_ids = False
                            if line['invoice_line_tax_ids']:
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
                    else:
                        _logger.info(f"Factura existente ID Externo {inv['id']}, Odoo17 ID {exist_invoice.id}")
                offset += limit


    def search_data(self, model, search_id):
        if search_id:
            return self.env[model].search([('odoo10_id', '=', search_id)], limit=1).id
        return False

    def exist_number(self, number, odoo10_id):
        move_id = self.search([('odoo10_id','=',odoo10_id)])
        if move_id:
            return move_id
        else:
            return False

    def register_paymet(self, inv_id, payments):
        for pay in payments:
            journal_id = self.env['account.journal'].search([('code','=',pay['journal_id'].get('code'))])
            if journal_id.currency_id:
                currency_id = journal_id.currency_id
            else:
                currency_id = self.env.user.company_id.currency_id

            values = {
                'amount': pay['amount'],
                'payment_date': pay['payment_date'],
                'journal_id': journal_id.id,
                'currency_id': currency_id.id,
                'communication': pay['communication']
            }

            if inv_id.move_type == 'in_invoice':
                values.update({'pay_method_type': pay['pay_method_type'], 'partner_type': 'supplier', 'payment_type': 'outbound'})
            elif inv_id.move_type == 'out_invoice':
                payment_method_line_id = journal_id._get_available_payment_method_lines('inbound')
                values.update({'partner_type': 'customer', 'payment_type': 'inbound', 'payment_method_line_id': payment_method_line_id.id})

            reconcilable_lines = inv_id.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled and l.balance != 0)
            line_id_to_reconcile = reconcilable_lines[0].id if reconcilable_lines else False
            if pay['apply_retentions']:
                ret_vals = []
                for ret in pay['retention_lines']:
                    inv_odoo10_id = ret.get('invoice_id')[0]
                    if inv_id.odoo10_id == inv_odoo10_id:
                        ret_values = {
                            'invoice_line_id': line_id_to_reconcile,
                            'amount': ret.get('amount'),
                            'amount_currency': ret.get('amount')
                        }

                        account = ret.get('account_id')[1]
                        code, name_account = account.split(maxsplit=1)
                        account_id = self.env['account.account'].search([('code', '=', code)])
                        if account_id:
                            ret_values.update({'account_id': account_id.id})
                            ret_values.update({'percentage': account_id.retention_porcent})
                        ret_vals.append((0, 0, ret_values))
                if len(ret_vals) > 0:
                    values.update({
                        'apply_retentions': True,
                        'retention_line_ids': ret_vals
                    })

            values.update({'line_ids': [(6, 0, reconcilable_lines.ids)]})
            if line_id_to_reconcile:
                payment_register_wizard = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=[line_id_to_reconcile]).create(values)
                payment_register_wizard.action_create_payments()
            else:
                _logger.info(f"No se pudo realizar el pago de la factura {inv_id.name}")

    def sync_moves(self, limit=500, opt='production'):
        company_id = self.env.user.company_id
        ip = '181.189.230.70'
        if opt == 'test':
            ip = '10.1.4.56'

        last_date = datetime.now().date() - timedelta(days=1)
        url = "http://%s:8000/get_moves?start_date=%s&end_date=%s&limit=%s"%(ip, '2025-06-09', '2025-06-09', limit)
        response = requests.get(url)

        if response.status_code == 200:
            moves = response.json()
            for mv in moves:
                exist = self.exist_number(mv['name'], mv['id'])
                if not exist:
                    values = {
                        'odoo10_id': mv['id'],
                        'ref': mv.get('ref'),
                        'date': mv['date'],
                        'name': mv['name'],
                        'internal_number': mv['name'],
                        'move_type': 'entry'
                    }
                    journal_id = self.env['account.journal'].search([('code','=',mv['journal_id'].get('code'))])
                    if journal_id:
                        values.update({'journal_id': journal_id.id})
                    move_id = self.create(values)
                    lines = []
                    for line in mv['line_ids']:
                        account = line['account_id'][1]
                        code, name_account = account.split(maxsplit=1)
                        account_id = self.env['account.account'].search([('code', '=', code)])
                        partner_id = False
                        if line['partner_id']:
                            partner_id = self.search_data('res.partner', line['partner_id'][0])

                        if not line.get('currency_id'):
                            currency_id = company_id.currency_id
                        else:
                            currency_id = self.env['res.currency'].search([('name', '=', line.get('currency_id')[1])])
                        
                        if line['credit'] > 0:
                            amount_currency = -line['credit']
                        elif line['debit'] > 0:
                            amount_currency = line['debit']

                        lines_values = {
                            'account_id': account_id.id,
                            'name': line['name'],
                            'partner_id': partner_id,
                            'debit': line['debit'],
                            'credit': line['credit'],
                            'currency_id': currency_id.id,
                            'amount_currency': amount_currency
                        }

                        lines.append((0, 0, lines_values))
                    move_id.update({'line_ids': lines})
                    
                    if mv['state'] == 'posted':
                        move_id.action_post()