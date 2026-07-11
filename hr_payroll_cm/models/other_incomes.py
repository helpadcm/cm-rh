from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class otherIncomes(models.Model):
    _name = 'hr.other.incomes'
    _description = 'Ingresos: Modelo para el agregar otros ingresos para calculo de planilla'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Descripcion",tracking=True)
    employee_id = fields.Many2one('hr.employee',string="Empleado", tracking=True)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Tipo', tracking=True)
    start_date = fields.Date(string="Fecha de Inicio", tracking=True)
    end_date = fields.Date(string="Fecha Final", tracking=True)
    amount = fields.Float(string="Monto", tracking=True)
    total_amount = fields.Float(string="Monto Total", tracking=True)
    state = fields.Selection([('draft','Borrador'),('in_progress','En proceso'),('completed','Completado')],string="Estado",default="draft", tracking=True)
    payslip_id = fields.Many2one('hr.payslip', string='Nomina')
    payment_plan_ids = fields.One2many('incomes.payment.plan','income_id',string="Plan de pago")
    payment_type = fields.Selection([('fortnight','Quincenal'),('monthly','Mensual')],string="Tipo de pago", default="fortnight")
    monthly_type = fields.Selection([('first','Primera'),('second','Segunda')],string="Quincena", default="first")
    quotes_number = fields.Integer(string="Cuotas")
    by_quotes = fields.Boolean(string="Por Cuotas")

    @api.onchange('input_type_id')
    def _onchange_input_type_id(self):
        self.name = self.input_type_id.name

    def change_state(self):
        self.state = 'in_progress'
        if self.by_quotes:
            self.create_plan()

    def send_draft(self):
        self.state = 'draft'

    @api.constrains('start_date','end_date')
    def _validate_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError('La fecha de inicio no puede ser mayor a la final')

    def finalize_incomes(self):
        income_ids = self.search([('state','=','in_progress')])
        if income_ids:
            for income in income_ids:
                if not income.by_quotes:
                    if income.payslip_id.state == 'paid':
                        income.write({'state':'completed'})
                else:
                    if income.payment_plan_ids:
                        finalize = True
                        for plan in income.payment_plan_ids:
                            if not plan.payslip_id:
                                finalize = False
                                break

                            if plan.state != 'paid':
                                finalize = False
                                break
                        
                        if finalize:
                            income.write({'state':'completed'})
        return True

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('No se pueden eliminar registros en progreso o completados')
        res = super(otherIncomes, self).unlink()
        return res

    def create_plan(self):
        if self.payment_plan_ids:
            states = set(self.payment_plan_ids.mapped('state'))
            if len(states) > 1:
                raise ValidationError("No se puede regenerar el plan por que ya hay cuotas pagadas")
            self.payment_plan_ids.unlink()

        initial_date = self.start_date
        if isinstance(initial_date, str):
            year, month, day = map(int, initial_date.split("-"))
            initial_date = date(year, month, day)

        quote_amount = round(self.amount / self.quotes_number, 2)
        plan = []
        
        if self.payment_type == "monthly":
            day = 1 if self.monthly_type == "first" else 16
            init_date = date(initial_date.year, initial_date.month, day)
        else:  # quincenal
            day = 1 if initial_date.day < 16 else 16
            init_date = date(initial_date.year, initial_date.month, day)

        for i in range(self.quotes_number):
            self.end_date = init_date
            vals = {
                "number": i + 1,
                "amount": quote_amount,
                'income_id': self.id,
                "date": init_date
            }
            self.env['incomes.payment.plan'].create(vals)

            if self.payment_type == "monthly":
                # sumar un mes
                init_date = init_date + relativedelta(months=1)
                init_date = init_date.replace(day=1 if self.monthly_type == "first" else 16)
            else:  # quincenal
                if init_date.day == 1:
                    init_date = init_date.replace(day=16)
                else:
                    init_date = (init_date + relativedelta(months=1)).replace(day=1)
            

class paymentPlanIncome(models.Model):
    _name = 'incomes.payment.plan'
    _description = 'Plan de pago ingresos'

    income_id = fields.Many2one('hr.other.incomes',string="Deduccion")
    number = fields.Integer(string="# Cuota")
    date = fields.Date(string="Fecha")
    state = fields.Selection(related='payslip_id.state',string="Estado")
    amount = fields.Float(string="Monto")
    payslip_id = fields.Many2one('hr.payslip',string="Nomina")

    def unlink(self):
        for val in self:
            if val.state == 'paid':
                raise ValidationError("No puede eliminar un registro pagado")
        return super(paymentPlanIncome, self).unlink()