# -*- coding: utf-8 -*-

import requests
import logging
from odoo import models, fields, api
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class accountMoveSync(models.Model):
    _inherit = 'account.move'

    odoo10_id = fields.Integer(string="Id Odoo 10")

    def sync_invoices(self, invoice_type, limit=1000):

        last_date = datetime.now().date() - timedelta(days=1)

        ##################    URL INVOICES COUNT ##########################################
        # url_inv_count = "http://10.1.4.56:8000/get_invoices_count?start_date=%s&end_date=%s&invoice_type=%s"%(last_date, last_date, invoice_type)
        url_inv_count = "http://181.189.230.70:8000/get_invoices_count?start_date=%s&end_date=%s&invoice_type=%s"%(last_date, last_date, invoice_type)
        response = requests.get(url_inv_count, timeout=60)
        _logger.info(f"Solicitando conteo de facturas de tipo '{invoice_type}' a: {url_inv_count}")
        
        count_response = requests.get(url_inv_count, timeout=60)
        total_items = count_response.json().get("total_invoices", 0)
        # if total_items == 0:
        #     _logger.info(f"No hay facturas de tipo '{invoice_type}' para sincronizar en el rango especificado. Pasando al siguiente tipo.")
        #     continue

        offset = 0
        while offset < total_items:
            ##################    URL INVOICES  ##########################################
            _logger.info(f"Solicitando tanda de facturas '{invoice_type}': skip={offset}, limit={limit}")
            # url = "http://10.1.4.56:8000/get_invoices?start_date=%s&end_date=%s&invoice_type=%s&skip=%s&limit=%s"%(last_date, last_date, invoice_type, offset, limit)
            url = "http://181.189.230.70:8000/get_invoices?start_date=%s&end_date=%s&invoice_type=%s&skip=%s&limit=%s"%(last_date, last_date, invoice_type, offset, limit)
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
                odoo10_cai_names = set() # CAI ID viene como [id, name] en tu API
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
                _logger.info(odoo10_partner_ids)
                _logger.info(odoo10_user_ids)
                _logger.info(currency_names)
                _logger.info(journal_codes)
                _logger.info(odoo10_cai_names)
                _logger.info(odoo10_payment_term_ids)
                offset += limit


    def search_data(self, model, odoo10_id):
        if search_id:
            return self.env[model].search([('odoo10_id', '=', search_id)], limit=1).id
        return False

    def exist_number(self, number, id_inv):
        if odoo10_id:
            # Es más robusto buscar por el ID del sistema origen (Odoo 10)
            return self.env['account.move'].sudo().search([('odoo10_id', '=', odoo10_id)], limit=1)
        elif move_name:
            # Como fallback, buscar por nombre de movimiento si no hay ID de Odoo 10 o es 'Borrador'
            return self.env['account.move'].sudo().search([('name', '=', move_name)], limit=1)
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
            payment_register_wizard = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=[line_id_to_reconcile]).create(values)
            payment_register_wizard.action_create_payments()