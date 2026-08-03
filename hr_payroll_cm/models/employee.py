from odoo import models, fields, api

selection_type = [
    ('one_line','Una Linea'),
    ('deduction','Tipo de deduccion'),
    ('employee','Por empleado'),
    ('department','Por departamento'),
]

class Employee(models.Model):
    _inherit = 'hr.employee'

    analytic_account_id = fields.Many2one('account.analytic.account',string="Cuenta Analitica")
    resident_number = fields.Char(string="Número de Residencia")

    def get_employee_no(self):
        for employee in self:
            employee.employee_no = employee.registration_number or employee.barcode or employee.pin or ''

class employeePublic(models.Model):
    _inherit = 'hr.employee.public'

    analytic_account_id = fields.Many2one('account.analytic.account',string="Cuenta Analitica")
    resident_number = fields.Char(string="Número de Residencia")

class EmployeeMembersInh(models.Model):
    _inherit = 'hr.employees.members'

    compensatory_day_string = fields.Char(related="employee_id.compensatory_day_string",string="Tiempo Compensatorio")
    available_vacations = fields.Float(related="employee_id.vacations_day",string="Vacaciones Disp.")

class payslipInputInherit(models.Model):
    _inherit = 'hr.payslip.input.type'

    active = fields.Boolean(string="Activo", default=True)
    entry_type = fields.Selection([('income', 'Ingreso'),('deduction', 'Deducción')], string="Tipo de entrada")

class departmentInherit(models.Model):
    _inherit = 'hr.department'

    calculate_hours = fields.Selection([('one','1 vez'),('two','2 veces')], string="Calculo Horas al Mes", default="two")
    analytic_account_id = fields.Many2one('account.analytic.account',string="Cuenta Analitica")
    priority_level = fields.Integer(string="Nivel de prioridad")

class salaryRulesInh(models.Model):
    _inherit = 'hr.salary.rule'

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        for rule in rules:
            rule_id = self.env['hr.inc.ded.rules'].search([('code','=',rule.code)])
            if not rule_id:
                self.env['hr.inc.ded.rules'].create({
                    'name': rule.name,
                    'code': rule.code,
                    'category_id': rule.category_id.id
                })
        return rules

class accountAccountInh(models.Model):
    _inherit = 'account.account'

    calculate_type = fields.Selection(selection_type, string="Tipo de Calculo", help="Campo para definir la forma en que se comportara la cuenta al crear el asiento contable de planillas")

class HrPayrollStructureTypeInh(models.Model):
    _inherit = 'hr.payroll.structure.type'

    def _get_selection_schedule_pay(self):
        return [
            ('annually', 'Anual'),
            ('semi-annually', 'Semestral'),
            ('quarterly', 'Trimestral'),
            ('bi-monthly', '2 meses'),
            ('monthly', 'Mensual'),
            ('semi-monthly', 'Quincenal'),
            ('bi-weekly', '2 semanas'),
            ('weekly', 'Semanal'),
            ('daily', 'Diario'),
        ]