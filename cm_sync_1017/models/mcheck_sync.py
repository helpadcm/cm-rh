# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api
from datetime import datetime, timedelta

class mcheckSync(models.Model):
    _inherit = 'mcheck.mcheck'

    create_odoo10 = fields.Datetime(string="Creado en odoo 10")

    def sync_mchecks(self, opt='production'):

        last_date = datetime.now().date() - timedelta(days=1)
        if self.env.context.get('start_date'):
            last_date = self.env.context.get('start_date')

        if self.env.context.get('opt'):
            opt = self.env.context.get('opt')

        # ip = '181.189.230.70'
        ip = '181.115.21.90'
        if opt == 'test':
            ip = '10.1.4.56'

        url = "http://%s:8000/get_mcheck?start_date=%s&end_date=%s"%(ip, last_date, last_date)
        response = requests.get(url)
        if response.status_code == 200:
            mchecks = response.json()
            for check in mchecks:
                exist = self.exist_number(check['number'])
                if not exist:
                    values = {
                        'number': check['number'],
                        'create_odoo10': check['create_date'],
                        'date': check['date'],
                        'doc_type': check['doc_type'],
                        'name': check['name'],
                        'total': check['total'],
                        'reference': check['reference'],
                    }

                    journal_id = self.env['account.journal'].search([('odoo10_id','=',check['journal_id'].get('id'))])
                    if journal_id:
                        values.update({'journal_id': journal_id.id})

                    mcheck_id = self.create(values)
                    user_id = self.env['res.users'].search([('odoo10_id','=',check['create_uid'][0])])
                    if user_id:
                        mcheck_id.write({'user_creator': user_id.id})
                    for line in check['mcheck_ids']:
                        account = line['account_id'][1]
                        code, name_account = account.split(maxsplit=1)
                        account_id = self.env['account.account'].search([('code', '=', code)])
                        
                        partner_id = False
                        if line['partner_id']:
                            partner_id = self.search_data('res.partner', line['partner_id'][0])
                        
                        self.env['mcheck.mcheck_name'].create({
                            'mcheck_id': mcheck_id.id,
                            'name': line['name'],
                            'partner_id': partner_id,
                            'type': line['type'],
                            'amount': line['amount'],
                            'account_id': account_id.id,
                        })
                    
                    if check['state'] == 'validated':
                        mcheck_id.action_validate()

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