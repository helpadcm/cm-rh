import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportGeneralLedger(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_general_ledger'

    def _get_account_move_entry(self, accounts, analytic_account_ids,
                                partner_ids, init_balance,
                                sortby, display_account,group_ledger=None,consolidate=None):
        """
        :param:
                accounts: the recordset of accounts
                analytic_account_ids: the recordset of analytic accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        initmove_lines= dict(map(lambda x: (x, []), accounts.ids))

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            context = dict(self.env.context)
            context['date_from'] = self.env.context.get('date_from')
            context['date_to'] = False
            context['initial_bal'] = True
            if analytic_account_ids:
                context['analytic_account_ids'] = analytic_account_ids
            if partner_ids:
                context['partner_ids'] = partner_ids
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(context)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            stament1=""
            stament2=""
            stament3=""
           
            if group_ledger == 'analytic':
            	stament1=", aaa.id AS analytic_id, MIN(fan.analytic_account) AS analytic_name"
            	stament2=""
            	stament3=", aaa.id"
            if group_ledger == 'partner':
            	stament1=", p.id AS partner_id, p.name AS partner_name"
            	stament3=", p.id"

            sql = (f"""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate,
                '' AS lcode, COALESCE(SUM(l.amount_currency),0.0) AS amount_currency, 
                MIN(fan.analytic_account) AS analytic_name,
                'Initial Balance' AS lname,
                COALESCE(SUM(aal.amount), 0.0) AS balance_analytic,
                COALESCE(SUM(l.debit),0.0) AS debit, 
                COALESCE(SUM(l.credit),0.0) AS credit, 
                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance
                {stament1},
                '' AS lpartner_id,\
                MIN(l.ref) AS lref,
                '' AS move_name, '' AS move_id, c.symbol AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                LEFT JOIN account_analytic_line aal ON aal.move_line_id = l.id
                LEFT JOIN account_analytic_account aaa ON aaa.id = aal.account_id
                LEFT JOIN LATERAL (
                    SELECT value AS analytic_account
                    FROM jsonb_each_text(aaa.name)
                    LIMIT 1
                ) AS fan ON true
                {stament2}
                WHERE l.account_id IN %s""" + filters + f""" GROUP BY l.account_id, c.symbol {stament3}""")
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                # move_lines[row.pop('account_id')].append(row)
                initmove_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        context = dict(self.env.context)
        if analytic_account_ids:
            context['analytic_account_ids'] = analytic_account_ids
        if partner_ids:
            context['partner_ids'] = partner_ids
        tables, where_clause, where_params = MoveLine.with_context(context)._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, 
            l.date AS ldate, j.code AS lcode, l.currency_id, 
            l.amount_currency, '' AS analytic_account_id,
            COALESCE(SUM(aal.amount), 0.0) AS analytic_amount,
            MIN(fan.analytic_account) AS analytic_name,
            aaa.id AS analytic_id,
            l.partner_id AS partner_id,
            l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, 
            COALESCE(l.credit,0) AS credit, 
            COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, 
            p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            LEFT JOIN account_analytic_line aal ON aal.move_line_id = l.id
            LEFT JOIN account_analytic_account aaa ON aaa.id = aal.account_id
            LEFT JOIN LATERAL (
                SELECT value AS analytic_account
                FROM jsonb_each_text(aaa.name)
                LIMIT 1
            ) AS fan ON true
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, 
            l.account_id, l.date, j.code, l.currency_id, l.amount_currency, 
            l.ref, l.name, m.name, c.symbol, p.name, aaa.id ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = self.merge_move(move_lines[account.id],initmove_lines[account.id],group_ledger,init_balance,consolidate)
            # res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                if line['lid']!=-1:
                    res['debit'] += float(line['debit'])
                    res['credit'] += float(line['credit'])
                    res['balance'] = res['debit'] - res['credit']
                res.update({'amount_currency':res.get('amount_currency',0) + line.get('amount_currency',0), 'currency_code': line.get('currency_code')})
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if consolidate:
                res['move_lines']= []
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        group_ledger = data['form'].get('group_ledger')
        consolidate = data['form'].get('consolidate')
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]

        analytic_account_ids = False
        if data['form'].get('analytic_account_ids', False):
            analytic_account_ids = self.env['account.analytic.account'].search(
                [('id', 'in', data['form']['analytic_account_ids'])])

        partner_ids = False
        if data['form'].get('partner_ids', False):
            partner_ids = self.env['res.partner'].search(
                [('id', 'in', data['form']['partner_ids'])])

        if model == 'account.account':
            accounts = docs
        else:
            domain = []
            if data['form'].get('account_ids', False):
                domain.append(('id', 'in', data['form']['account_ids']))
            accounts = self.env['account.account'].search(domain)

        accounts_res = self.with_context(
            data['form'].get('used_context', {}))._get_account_move_entry(
            accounts,
            analytic_account_ids,
            partner_ids,
            init_balance, sortby, display_account,group_ledger=group_ledger,consolidate=consolidate)
        cont=0
        if init_balance:
            cont=1
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            'accounts': accounts,
            'partner_ids': partner_ids,
            'analytic_account_ids': analytic_account_ids,
            'init_balance':cont,
        }

    @api.model
    def render_xls(self, docids, data={}):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = data.get('context').get('active_model')
        docs = self.env[model].browse(docids)
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        group_ledger = data['form'].get('group_ledger')
        consolidate = data['form'].get('consolidate')
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]

        analytic_account_ids = False
        if data['form'].get('analytic_account_ids', False):
            analytic_account_ids = self.env['account.analytic.account'].search(
                [('id', 'in', data['form']['analytic_account_ids'])])

        partner_ids = False
        if data['form'].get('partner_ids', False):
            partner_ids = self.env['res.partner'].search(
                [('id', 'in', data['form']['partner_ids'])])

        if model == 'account.account':
            accounts = docs
        else:
            domain = []
            if data['form'].get('account_ids', False):
                domain.append(('id', 'in', data['form']['account_ids']))
            accounts = self.env['account.account'].search(domain)
            
        accounts_res = self.with_context(
            data['form'].get('used_context', {}))._get_account_move_entry(
            accounts,
            analytic_account_ids,
            partner_ids,
            init_balance, sortby, display_account,group_ledger=group_ledger,consolidate=consolidate)
        cont=0
        if init_balance:
            cont=1
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            'accounts': accounts,
            'partner_ids': partner_ids,
            'analytic_account_ids': analytic_account_ids,
            'init_balance':cont,
        }

    @api.model
    def merge_move(self, move_lines, initmove_lines, group_ledger, init_balance, consolidate):
        res = []
        if not group_ledger:
            res = initmove_lines + move_lines
        
        if group_ledger == 'partner':
            partner_ids = list(set(map(lambda line: line.get('partner_id'), move_lines + initmove_lines)))
            for partner in self.env['res.partner'].browse(partner_ids):
                inifilters = filter(lambda line: line['partner_id'] == partner.id, initmove_lines)
                init_bal = 0.0
                init_deb = 0.0
                init_cre = 0.0
                amount_currency = 0.0
                lname = ''
                pname = partner.name
                if not partner.id:
                    pname =_('Without Partner')
                for initfil in inifilters:
                    init_cre = initfil.get('credit',0.0)
                    init_deb = initfil.get('debit',0.0)
                    amount_currency = initfil.get('amount_currency',0.0)
                    init_bal = init_deb - init_cre
                    lname = initfil.get('lname','')
                line = self.init_data(init_bal, init_deb, init_cre, partner.id, None, None, pname, lname, amount_currency)
                res.append(line)
                filters = filter(lambda line: line['partner_id'] == partner.id, move_lines)
                bal = init_bal
                for fil in filters:
                    bal += fil.get('debit',0.0)-fil.get('credit',0.0)
                    fil['balance'] = bal
                    res.append(fil)
                res.append(self.sum_total(bal,partner.id,None,None))
        if group_ledger == 'analytic':
            analytic_ids=list(set(map(lambda line: line.get('analytic_id'), move_lines+initmove_lines)))
            for analytic in self.env.get('account.analytic.account').browse(analytic_ids):
                inifilters= filter(lambda line: line['analytic_id'] == analytic.id, initmove_lines)
                init_bal = 0.0
                init_deb = 0.0
                init_cre = 0.0
                amount_currency = 0.0
                lname = ''
                pname = analytic.name
                if not analytic.id:
                    pname=_('Sin Analitica')
                for initfil in inifilters:
                    if pname != 'Sin Analitica':
                        if initfil.get('debit') != 0 and initfil.get('credit') == 0:
                            init_deb += abs(initfil.get('balance_analytic', 0))

                        if initfil.get('credit') != 0 and initfil.get('debit') == 0:
                            init_cre += abs(initfil.get('balance_analytic', 0))
                        # amount_currency = abs(initfil.get('amount_currency', 0))
                    else:
                        init_cre += initfil.get('credit',0.0)
                        init_deb += initfil.get('debit',0.0)
                    amount_currency = initfil.get('amount_currency',0.0)
                    lname = initfil.get('lname','')
                init_bal = init_deb - init_cre
                line = self.init_data(init_bal, init_deb, init_cre, None, analytic.id, None, pname, lname, amount_currency)
                res.append(line)
                filters= filter(lambda line: line['analytic_id'] == analytic.id, move_lines)
                bal = init_bal
                for fil in filters:
                    if pname != 'Sin Analitica':
                        if fil.get('debit') != 0 and fil.get('credit') == 0:
                            fil['debit'] = abs(fil.get('analytic_amount'))

                        if fil.get('credit') != 0 and fil.get('debit') == 0:
                            fil['credit'] = abs(fil.get('analytic_amount'))

                    if fil.get('currency_code') == 'L':
                        fil['amount_currency'] = abs(fil.get('analytic_amount'))
                    bal += fil.get('debit',0.0)-fil.get('credit',0.0)
                    fil['balance'] = bal
                    res.append(fil)
                res.append(self.sum_total(bal,None,analytic.id,None))

        return res

    @api.model
    def init_data(self, bal, deb, cre, partner_id, analytic_id, account_id, name, lname, amount_currency):
        res={	
            'lid': 0, 
            'lpartner_id': '', 
            'partner_id': partner_id, 
            'analytic_id': analytic_id,
            'account_id': account_id,     		
            'invoice_type': '', 
            'invoice_id': '', 
            'currency_id': None, 
            'debit': deb, 
            'move_name': '', 
            'lname': lname, 
            'credit': cre, 
            'mmove_id': '', 
            'partner_name': name, 
            'currency_code': None, 
            'lref': '', 
            'amount_currency': amount_currency, 
            'balance': bal,
            'invoice_number': '', 
            'lcode': '', 'ldate': ''}
        return res

    @api.model
    def sum_total(self, bal, partner_id, analytic_id, account_id):
        res={	'lid': -1, 
            'lpartner_id': '', 
            'partner_id': partner_id, 
            'analytic_id':analytic_id,
            'account_id': account_id,     		
            'invoice_type': '', 
            'invoice_id': '', 
            'currency_id': None, 
            'debit': 0, 
            'move_name': '', 
            'lname': 'TOTAL', 
            'credit': 0, 
            'mmove_id': '', 
            'partner_name': None, 
            'currency_code': None, 
            'lref': '', 
            'amount_currency': 0.0, 
            'balance': bal,
            'invoice_number': '', 
            'lcode': '', 'ldate': ''}
        return res