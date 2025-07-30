from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    type_lot = fields.Selection([('normal','Normal'),('fourteenth','Decimo Cuarto Mes'),('thirteenth','Decimo Tercer Mes')], string="Tipo de lote", default="normal")
    journal_id = fields.Many2one('account.journal',string="Diario")

    @api.onchange('date_start', 'type_lot')
    def get_payslip_name(self):
        if self.type_lot == 'normal':
            if self.date_start:
                if self.date_start.day == 1:
                    self.name = '1ra Quincena mes %s del año %s'%(months[self.date_start.month - 1], self.date_start.year)
                if self.date_start.day == 16:
                    self.name = '2da Quincena mes %s del año %s'%(months[self.date_start.month - 1], self.date_start.year)
        else:
            if self.type_lot == 'fourteenth':
                self.name = 'Decimo Cuarto Mes año %s'%(self.date_end.year)
            elif self.type_lot == 'thirteenth':
                self.name = 'Decimo Tercer Mes año %s'%(self.date_start.year)

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
        vals = {
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'ref': f"Asiento generado desde lote {self.name}",
            'date': self.date_end
        }

        move_lines = []
        departments_values = []
        department_list = self.slip_ids.mapped('employee_id.department_id')
        for dep in department_list:
            account_list = []
            account_values = []
            slip_ids = self.slip_ids.filtered(lambda slip: slip.employee_id.department_id.id == dep.id)
            for sl in slip_ids:
                for line in sl.line_ids:
                    if not line.salary_rule_id.account_debit and not line.salary_rule_id.account_credit:
                        continue

                    if line.salary_rule_id.account_debit.id in account_list:
                        account_values[account_list.index(line.salary_rule_id.account_debit.id)]['amount'] += line.total
                    else:
                        account_list.append(line.salary_rule_id.account_debit.id)
                        account_values.append({
                            'account_id': line.salary_rule_id.account_debit.id,
                            'amount': line.total,
                            'type': 'debit'
                        })

                    if line.salary_rule_id.account_credit.id in account_list:
                        account_values[account_list.index(line.salary_rule_id.account_credit.id)]['amount'] += abs(line.total)
                    else:
                        account_list.append(line.salary_rule_id.account_credit.id)
                        account_values.append({
                            'account_id': line.salary_rule_id.account_credit.id,
                            'amount': abs(line.total),
                            'type': 'credit'
                        })

            departments_values.append({
                'department_name': dep.name,
                'analytic_account': dep.analytic_account_id.id or False,
                'lines': account_values
            })

        total_debit = 0
        total_credit = 0
        for department in departments_values:
            for l in department.get('lines'):
                if l.get('account_id') and l.get('amount') > 0:
                    values = {
                        'name': self.name,
                        'account_id': l.get('account_id'),
                    }
                    if department.get('analytic_account'):
                        distribution_line = {str(department.get('analytic_account')): 100.0}
                        values.update({'analytic_distribution': distribution_line})

                    if l.get('type') == 'debit':
                        values.update({'debit': l.get('amount'), 'amount_currency': l.get('amount')})
                        total_debit += l.get('amount')

                    if l.get('type') == 'credit':
                        values.update({'credit': l.get('amount'), 'amount_currency': -l.get('amount')})
                        total_credit += l.get('amount')
                    
                    move_lines.append((0, 0, values))
        
        if not self.journal_id.default_account_id:
            raise ValidationError(f"Debe configurar una cuenta por defecto en el diario {self.journal_id.name}")

        last_line = move_lines.append((0, 0, {
            'name': self.name,
            'account_id': self.journal_id.default_account_id.id,
            'credit': total_debit - total_credit,
            'amount_currency': (total_debit - total_credit) * -1
        }))

        vals.update({'line_ids': move_lines})
        move_id = self.env['account.move'].create(vals)
        self.slip_ids.write({'move_id': move_id.id})
