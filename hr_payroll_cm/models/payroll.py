from math import ceil

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    first_date_payment = fields.Date(
        'Fecha de inicio de pago',
        compute='_compute_first_date_payment',
        help='Fecha de comienzo de pagos', )
    payment_plan_ids = fields.One2many('deductions.payment.plan','deduction_id',string="Plan de pago")
    payment_type = fields.Selection([('fortnight','Quincenal'),('monthly','Mensual')],string="Tipo de pago", default="fortnight")
    monthly_type = fields.Selection([('first','Primera'),('second','Segunda')],string="Quincena", default="first")
    quotes_number = fields.Integer(string="Cuotas")
    by_quotes = fields.Boolean(string="Por Cuotas")
    fixed_fee = fields.Float(string="Cuota fija")
    total_amount = fields.Monetary('Monto Total',tracking=True,help='Total amount to be paid.',default=1)
    monthly_amount = fields.Monetary('Monto a debitar', required=True, tracking=True, help='Amount to pay each month.',default=1)
    estimated_end = fields.Date('Estimated End Date', help='Approximated end date.', tracking=True)

    def update_estimated_date(self):
        if self.date_estimated_end:
            self.estimated_end = self.date_estimated_end
        if self.date_end:
            self.estimated_end =  self.date_end

    @api.onchange('payment_plan_ids')
    def onchange_amount(self):
        if self.payment_plan_ids:
            self.total_amount = sum(self.payment_plan_ids.mapped('amount'))

    @api.depends('state', 'total_amount', 'monthly_amount', 'date_start', 'payment_plan_ids','estimated_end')
    def _compute_estimated_end(self):
        for record in self:
            if not record.payment_plan_ids:
                record.date_estimated_end = record.estimated_end
                record.date_end = record.estimated_end
                # if record.state not in ['close', 'cancel'] and record.total_amount and record.monthly_amount:
                #     payments = record._compute_number_of_payments(record.total_amount, record.monthly_amount)
                #     record._compute_date_estimated_end(payments)
                # else:
                #     record.date_estimated_end = False
            else:
                record.date_estimated_end = record.payment_plan_ids[len(record.payment_plan_ids)-1].date
                record.date_end = record.payment_plan_ids[len(record.payment_plan_ids)-1].date

    @staticmethod
    def _compute_number_of_payments(total_amount, monthly_amount):
        if monthly_amount == 0:
            return 0
        number_of_payments = ceil(total_amount / monthly_amount)
        return number_of_payments

    @api.depends('date_start')
    def _compute_first_date_payment(self):
        for record in self:
            if record.date_start.day > 16:
                record.first_date_payment = record.date_start + relativedelta(months=1, day=1)
            elif record.date_start.day == 1:
                record.first_date_payment = record.date_start
            else:
                record.first_date_payment = record.date_start + relativedelta(day=16)

    def _compute_date_estimated_end(self, number_of_payments):
        for record in self:
            first_date = record.first_date_payment
            current_date = first_date

            for _ in range(number_of_payments - 1):  # Iteramos hasta el último pago
                if current_date.day <= 15:  
                    # Si está en la primera quincena (1-15), ir al día 16>
                    current_date = current_date + relativedelta(day=15)
                else:  
                    # Si está en la segunda quincena (16-fin de mes), ir al día 1 del próximo mes
                    current_date = current_date + relativedelta(months=1, day=1)
            
            record.date_estimated_end = current_date
            record.date_end = current_date

    def create_plan(self):
        if self.payment_plan_ids:
            states = set(self.payment_plan_ids.mapped('state'))
            if len(states) > 1:
                raise ValidationError("No se puede regenerar el plan por que ya hay cuotas pagadas")
            self.payment_plan_ids.unlink()

        initial_date = self.date_start
        if isinstance(initial_date, str):
            year, month, day = map(int, initial_date.split("-"))
            initial_date = date(year, month, day)

        if self.fixed_fee > 0:
            quote_amount = self.fixed_fee
        else:
            if self.quotes_number == 0:
                raise ValidationError("El numero de cuotas no puede ser 0")
                
            quote_amount = round(self.total_amount / self.quotes_number, 2)

        self.total_amount = self.quotes_number * quote_amount
        plan = []

        self.monthly_amount = quote_amount
        
        if self.payment_type == "monthly":
            day = 1 if self.monthly_type == "first" else 16
            init_date = date(initial_date.year, initial_date.month, day)
        else:  # quincenal
            day = 1 if initial_date.day < 16 else 16
            init_date = date(initial_date.year, initial_date.month, day)

        for i in range(self.quotes_number):
            vals = {
                "number": i + 1,
                "amount": quote_amount,
                'deduction_id': self.id,
                "date": init_date
            }
            self.env['deductions.payment.plan'].create(vals)

            if self.payment_type == "monthly":
                # sumar un mes
                init_date = init_date + relativedelta(months=1)
                init_date = init_date.replace(day=1 if self.monthly_type == "first" else 16)
            else:  # quincenal
                if init_date.day == 1:
                    init_date = init_date.replace(day=16)
                else:
                    init_date = (init_date + relativedelta(months=1)).replace(day=1)
            self.date_end = self.payment_plan_ids[len(self.payment_plan_ids) - 1].date
            self.estimated_end = self.payment_plan_ids[len(self.payment_plan_ids) - 1].date

    @api.onchange('deduction_type_id')
    def get_deduction_name(self):
        if self.deduction_type_id:
            self.description = self.deduction_type_id.name

    def update_paid_amount(self):
        if self.by_quotes:
            self.paid_amount = 0
            for line in self.payment_plan_ids:
                if line.state == 'paid':
                    self.paid_amount += line.amount

    def finalize_deductions(self):
        deduction_ids = self.search([('state','=','open')])
        for ded in deduction_ids:
            if ded.remaining_amount == 0:
                ded.state = 'close'

class paymentPlanDed(models.Model):
    _name = 'deductions.payment.plan'
    _description = 'Plan de pago deducciones'

    deduction_id = fields.Many2one('hr.salary.attachment',string="Deduccion")
    number = fields.Integer(string="# Cuota")
    date = fields.Date(string="Fecha")
    state = fields.Selection(related='payslip_id.state',string="Estado")
    amount = fields.Float(string="Monto")
    payslip_id = fields.Many2one('hr.payslip',string="Nomina")

    def unlink(self):
        for val in self:
            if val.state == 'paid':
                raise ValidationError("No puede eliminar un registro pagado")
            val.deduction_id.paid_amount -= val.amount
        return super(paymentPlanDed, self).unlink()

    @api.onchange('state')
    def update_paid_amount(self):
        if self.state == 'paid':
            self.deduction_id.paid_amount += self.amount