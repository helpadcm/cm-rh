# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api
from datetime import datetime, timedelta

class depositSync(models.Model):
    _inherit = 'banks.deposit'

    def sync_deposits(self, opt='production'):
        last_date = datetime.now().date() - timedelta(days=1)
        if self.env.context.get('start_date'):
            last_date = self.env.context.get('start_date')

        if self.env.context.get('opt'):
            opt = self.env.context.get('opt')

        ip = '181.189.230.70'
        if opt == 'test':
            ip = '10.1.4.56'

        url = "http://%s:8000/get_deposit?start_date=%s&end_date=%s"%(ip, last_date, last_date)
        response = requests.get(url)
        
        if response.status_code == 200:
            deposits = response.json()
            for dep in deposits:
                exist = self.exist_number(dep['number'])
                if not exist:
                    values = {
                        'number': dep['number'],
                        'date': dep['date'],
                        'doc_type': dep['doc_type'],
                        'name': dep['name'],
                        'total': dep['total'],
                    }

                    journal_id = self.env['account.journal'].search([('odoo10_id','=',dep['journal_id'].get('id'))])
                    if journal_id:
                        values.update({'journal_id': journal_id.id})

                    deposit_id = self.create(values)
                    for line in dep['mcheck_ids']:
                        account = line['account_id'][1]
                        code, name_account = account.split(maxsplit=1)
                        account_id = self.env['account.account'].search([('code', '=', code)])
                        
                        partner_id = False
                        if line['partner_id']:
                            partner_id = self.search_data('res.partner', line['partner_id'][0])
                        
                        self.env['banks.deposit.name'].create({
                            'mcheck_id': deposit_id.id,
                            'name': line['name'],
                            'partner_id': partner_id,
                            'type': line['type'],
                            'amount': line['amount'],
                            'account_id': account_id.id,
                        })
                    
                    if dep['state'] == 'validated':
                        deposit_id.action_validate()

    def search_data(self, model, search_id):
        if search_id:
            return self.env[model].search([('odoo10_id', '=', search_id)], limit=1).id
        return False

    def exist_number(self, number):
        check_id = self.search([('number','=',number)])
        if check_id:
            return True
        else:
            return False