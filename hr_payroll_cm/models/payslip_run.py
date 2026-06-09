from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'


    @api.model
    def get_journal_default(self):
        journal_default_id = self.env['account.journal'].search([('code','=','VARIO')])
        return journal_default_id.id

    type_lot = fields.Selection([('normal','Normal'),('fourteenth','Decimo Cuarto Mes'),('thirteenth','Decimo Tercer Mes')], string="Tipo de lote", default="normal")
    for_pilot = fields.Boolean(string="Para Pilotos")
    journal_id = fields.Many2one('account.journal',string="Diario", default=get_journal_default)

    @api.model_create_multi
    def create(self, vals_list):
        formated_date_cache = {}
        for vals in vals_list:
            # vals.update({'name': self.get_payslip_name()})
            if vals.get('journal_id'):
                id_journal = vals.get('journal_id')['id']
                vals.update({'journal_id': id_journal})
        return super().create(vals_list)

    def _get_name_for_period(self, vals=None, cache=None):
        res = super(HrPayslipRun, self)._get_name_for_period(vals, cache)
        lot_name = False
        extra_name = ''
        if vals.get('for_pilot'):
            extra_name = 'Pilotos'

        if vals.get('type_lot') == 'normal':
            if vals.get('date_start'):
                start_date = datetime.strptime(vals.get('date_start'), '%Y-%m-%d').date()
                if start_date.day == 1:
                    lot_name = f"""1ra Quincena mes {months[start_date.month - 1]} del año {start_date.year} {extra_name}"""
                if start_date.day == 16:
                    lot_name = f"""2da Quincena mes {months[start_date.month - 1]} del año {start_date.year} {extra_name}"""
        else:
            if vals.get('date_end'):
                date_end = datetime.strptime(vals.get('date_end'), '%Y-%m-%d').date()
                if vals.get('type_lot') == 'fourteenth':
                    lot_name = f"""Decimo Cuarto Mes año {date_end.year} {extra_name}"""
                elif vals.get('type_lot') == 'thirteenth':
                    lot_name = f"""Decimo Tercer Mes año {date_end.year} {extra_name}"""
        
        if lot_name:
            return lot_name
        else:
            return res

    def action_load_nomina_from_excel_wizard(self):
        """
        Open the wizard to load the payroll from an excel file.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.nomina.from.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_run_id': self.id
                }
            }

    def action_load_catorceavo_from_excel_wizard(self):
        """
        Open the wizard to load the catorceavo from an excel file.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.catorceavo.from.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_run_id': self.id
                }
            }

    def action_hr_payroll_payslips_report(self):
        """
        Load the payroll report in the system.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payroll.payslips.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'payslip_run_id': self.id,
                },
            }

    def action_paid(self):
        res = super(HrPayslipRun, self).action_paid()
        self.create_move()
        return res

    def create_move(self):
        vals_move = {
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'ref': f"Asiento generado desde lote {self.name}",
            'state': 'draft',
            'date': self.date_end
        }

        one_line_account_ids = self.env['account.account'].search([('calculate_type','=','one_line')])
        department_account_ids = self.env['account.account'].search([('calculate_type','=','department')])
        employee_account_ids = self.env['account.account'].search([('calculate_type','=','employee')])
        deduction_account_ids = self.env['account.account'].search([('calculate_type','=','deduction')])

        one_line_list = []
        one_line_values = []

        employee_list = []
        employee_values = []

        deduction_list = []
        deduction_values = []

        department_list = []
        department_values = []
        for sl in self.slip_ids:
            overtime_amount = 0
            if sl.worked_days_line_ids:
                for entry in sl.worked_days_line_ids:
                    if entry.work_entry_type_id.code == 'OVERTIME':
                        account_id = self.env['account.account'].search([('code','=','511.04')])
                        vals = {
                            'type': 'debit',
                            'account_id':account_id.id,
                            'employee': sl.employee_id.name,
                            'amount': entry.amount, 
                            'rule_name': account_id.name, 
                            'account_name': account_id.name,
                            'department': sl.employee_id.department_id.name
                        }
                        overtime_amount += entry.amount
                        if sl.employee_id.department_id.id in department_list:
                            department_values[department_list.index(sl.employee_id.department_id.id)]['lines'].append(vals)
                        else:
                            department_list.append(sl.employee_id.department_id.id)
                            department_values.append({
                                'name': sl.employee_id.department_id.name,
                                'id': sl.employee_id.department_id.id,
                                'analytic_account': sl.employee_id.department_id.analytic_account_id.id or False,
                                'type': 'department',
                                'lines': [vals]
                            })

            for line in sl.line_ids:
                if not line.salary_rule_id.account_debit and not line.salary_rule_id.account_credit:
                    continue

                if line.category_id.code == 'DED':
                    attachment_id = sl.salary_attachment_ids.filtered(lambda att: att.other_input_type_id.code == line.salary_rule_id.code)
                    if attachment_id:
                        if len(attachment_id) > 1:
                            for att in attachment_id:
                                total_att = 0
                                if not att.by_quotes:
                                    total_att = att.monthly_amount
                                else:
                                    line_id = att.payment_plan_ids.filtered(lambda plan: plan.date == sl.date_from)
                                    if line_id:
                                        total_att = line_id.amount
                                att.paid_amount += abs(total_att)
                        else:
                            attachment_id.paid_amount += abs(line.total)

                if abs(line.total) > 0:
                    vals = {'employee': sl.employee_id.name,'amount': line.total, 'rule_name': line.salary_rule_id.name, 'department': sl.employee_id.department_id.name}

                    if line.salary_rule_id.account_debit:
                        vals.update({
                            'type': 'debit', 
                            'account_id': line.salary_rule_id.account_debit.id, 
                            'account_name': line.salary_rule_id.account_debit.name
                        })
                        if line.salary_rule_id.account_debit.id in one_line_account_ids.ids:
                            if line.salary_rule_id.account_debit.id in one_line_list:
                                one_line_values[one_line_list.index(line.salary_rule_id.account_debit.id)]['lines'].append(vals)
                            else:
                                one_line_list.append(line.salary_rule_id.account_debit.id)
                                one_line_values.append({
                                    'name': line.salary_rule_id.name,
                                    'type': 'one_line',
                                    'lines':[vals]
                                })

                        if line.salary_rule_id.account_debit.id in employee_account_ids.ids:
                            if sl.employee_id.id in employee_list:
                                employee_values[employee_list.index(sl.employee_id.id)]['lines'].append(vals)
                            else:
                                employee_list.append(sl.employee_id.id)
                                employee_values.append({
                                    'name': sl.employee_id.name,
                                    'id': sl.employee_id.id,
                                    'analytic_account': sl.employee_id.analytic_account_id.id or False,
                                    'type': 'employee',
                                    'lines': [vals]
                                })

                        if line.salary_rule_id.account_debit.id in deduction_account_ids.ids:
                            if line.salary_rule_id.code in deduction_list:
                                deduction_values[deduction_list.index(line.salary_rule_id.code)]['lines'].append(vals)
                            else:
                                deduction_list.append(line.salary_rule_id.code)
                                deduction_values.append({
                                    'name': line.salary_rule_id.name,
                                    'id': line.salary_rule_id.id,
                                    'type': 'deduction',
                                    'lines':[vals]
                                })

                        if line.salary_rule_id.account_debit.id in department_account_ids.ids:
                            if line.salary_rule_id.account_debit.code == '511.01':
                                vals.update({'amount': line.total - overtime_amount})

                            if sl.employee_id.department_id.id in department_list:
                                department_values[department_list.index(sl.employee_id.department_id.id)]['lines'].append(vals)
                            else:
                                department_list.append(sl.employee_id.department_id.id)
                                department_values.append({
                                    'name': sl.employee_id.department_id.name,
                                    'id': sl.employee_id.department_id.id,
                                    'analytic_account': sl.employee_id.department_id.analytic_account_id.id or False,
                                    'type': 'department',
                                    'lines': [vals]
                                })

                    if line.salary_rule_id.account_credit:
                        vals.update({
                            'type': 'credit', 
                            'account_id': line.salary_rule_id.account_credit.id,
                            'account_name': line.salary_rule_id.account_credit.name
                        })
                        if line.salary_rule_id.account_credit.id in one_line_account_ids.ids:
                            if line.salary_rule_id.account_credit.id in one_line_list:
                                one_line_values[one_line_list.index(line.salary_rule_id.account_credit.id)]['lines'].append(vals)
                            else:
                                one_line_list.append(line.salary_rule_id.account_credit.id)
                                one_line_values.append({
                                    'name': line.salary_rule_id.name,
                                    'type': 'one_line',
                                    'lines':[vals]
                                })

                        if line.salary_rule_id.account_credit.id in employee_account_ids.ids:
                            if sl.employee_id.id in employee_list:
                                employee_values[employee_list.index(sl.employee_id.id)]['lines'].append(vals)
                            else:
                                employee_list.append(sl.employee_id.id)
                                employee_values.append({
                                    'name': sl.employee_id.name,
                                    'id': sl.employee_id.id,
                                    'analytic_account': sl.employee_id.analytic_account_id.id or False,
                                    'type': 'employee',
                                    'lines': [vals]
                                })

                        if line.salary_rule_id.account_credit.id in deduction_account_ids.ids:
                            if line.salary_rule_id.code in deduction_list:
                                deduction_values[deduction_list.index(line.salary_rule_id.code)]['lines'].append(vals)
                            else:
                                deduction_list.append(line.salary_rule_id.code)
                                deduction_values.append({
                                    'name': line.salary_rule_id.name,
                                    'id': line.salary_rule_id.id,
                                    'type': 'deduction',
                                    'lines':[vals]
                                })

                        if line.salary_rule_id.account_credit.id in department_account_ids.ids:
                            if line.salary_rule_id.account_credit.code == '511.01':
                                vals.update({'amount': line.total - overtime_amount})

                            if sl.employee_id.department_id.id in department_list:
                                department_values[department_list.index(sl.employee_id.department_id.id)]['lines'].append(vals)
                            else:
                                department_list.append(sl.employee_id.department_id.id)
                                department_values.append({
                                    'name': sl.employee_id.department_id.name,
                                    'id': sl.employee_id.department_id.id,
                                    'analytic_account': sl.employee_id.department_id.analytic_account_id.id or False,
                                    'type': 'department',
                                    'lines': [vals]
                                })

        move_lines = []
        t_total_debit = 0
        t_total_credit = 0
        for e in one_line_values:
            total_debit = 0
            total_credit = 0
            values = {
                'name': e.get('name')
            }
            for l in e.get('lines'):
                values.update({'account_id': l.get('account_id')})
                if l.get('type') == 'debit':
                    total_debit += l.get('amount')
                    t_total_debit += l.get('amount')

                if l.get('type') == 'credit':
                    total_credit += l.get('amount')
                    t_total_credit += l.get('amount')

            if total_credit < 0:
                total_credit =  total_credit * -1

            values.update({'credit': (total_credit), 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
            move_lines.append((0, 0, values))

        for emp in employee_values:
            total_debit = 0
            total_credit = 0
            employee_ids = []
            values = {
                'name': emp.get('name')
            }
            for l in emp.get('lines'):
                values.update({'account_id': l.get('account_id')})
                if emp.get('analytic_account'):
                    distribution_line = {str(emp.get('analytic_account')): 100.0}
                    values.update({'analytic_distribution': distribution_line})

                if l.get('type') == 'debit':
                    total_debit += l.get('amount')
                    t_total_debit += l.get('amount')

                if l.get('type') == 'credit':
                    total_credit += l.get('amount')
                    t_total_credit += l.get('amount')

                # values.update({'credit': (total_credit * -1), 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
            if total_credit < 0:
                total_credit =  total_credit * -1

            values.update({'credit': (total_credit), 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
            move_lines.append((0, 0, values))

        for ded in deduction_values:
            total_debit = 0
            total_credit = 0
            employee_ids = []
            values = {
                'name': ded.get('name')
            }
            for l in ded.get('lines'):
                values.update({'account_id': l.get('account_id')})
                if l.get('type') == 'debit':
                    total_debit += l.get('amount')
                    t_total_debit += l.get('amount')

                if l.get('type') == 'credit':
                    total_credit += l.get('amount')
                    t_total_credit += l.get('amount')

                # values.update({'credit': total_credit, 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
            if total_credit < 0:
                total_credit =  total_credit * -1

            values.update({'credit': (total_credit), 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
            move_lines.append((0, 0, values))

        for dep in department_values:
            employee_ids = []
            account_names = []
            department_values = []
            for l in dep.get('lines'):
                if l.get('account_name') in account_names:
                    department_values[account_names.index(l.get('account_name'))]['amount'] += l.get('amount')
                else:
                    account_names.append(l.get('account_name'))
                    department_values.append(l)

            for val in department_values:
                total_debit = 0
                total_credit = 0
                values = {
                    'name': f"{val.get('account_name')} {dep.get('name')}", 
                    'account_id': val.get('account_id')
                }
                if dep.get('analytic_account'):
                    distribution_line = {str(dep.get('analytic_account')): 100.0}
                    values.update({'analytic_distribution': distribution_line})

                if val.get('type') == 'debit':
                    total_debit = val.get('amount')
                    t_total_debit += val.get('amount')

                if l.get('type') == 'credit':
                    total_credit = val.get('amount')
                    t_total_credit += val.get('amount')

                if total_credit < 0:
                    total_credit =  total_credit * -1

                values.update({'credit': (total_credit), 'debit': total_debit, 'amount_currency': total_debit - abs(total_credit)})
                move_lines.append((0, 0, values))
        
        if not self.journal_id.default_account_id:
            raise ValidationError(f"Debe configurar una cuenta por defecto en el diario {self.journal_id.name}")

        if (t_total_debit - abs(t_total_credit)) > 0:
            credit_amount = t_total_debit - abs(t_total_credit)
            last_line = move_lines.append((0, 0, {
                'name': self.name,
                'account_id': self.journal_id.default_account_id.id,
                'credit': credit_amount,
                'amount_currency': (t_total_debit - abs(t_total_credit)) * -1
            }))

        vals_move.update({'line_ids': move_lines})
        move_id = self.env['account.move'].create(vals_move)
        self.slip_ids.write({'move_id': move_id.id})

    def print_payslip_report(self):
        return self.env.ref('hr_payroll_cm.action_lot_report_cm_xlsx').report_action(self)