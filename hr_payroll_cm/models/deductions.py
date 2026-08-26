from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class otherDeductions(models.Model):
    _name = 'hr.other.deductions'
    _description = 'Deducciones: Modelo para agregar otras deducciones para calculo de planilla'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Descripcion",tracking=True)
    employee_id = fields.Many2one('hr.employee',string="Empleado", tracking=True)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Tipo', tracking=True)
    start_date = fields.Date(string="Fecha de Inicio", tracking=True)
    end_date = fields.Date(string="Fecha Final", tracking=True)
    amount = fields.Float(string="Monto", tracking=True)
    total_amount = fields.Float(string="Monto Total", tracking=True)
    state = fields.Selection([('draft','Borrador'),('in_progress','En proceso'),('completed','Completado'),('cancel','Cancelado')],string="Estado",default="draft", tracking=True)
    payslip_id = fields.Many2one('hr.payslip', string='Nomina')
    rec_deduction_id = fields.Many2one('hr.salary.attachment',string="Rec. Deduccion")
    payment_plan_ids = fields.One2many('other.deductions.payment.plan','other_deduction_id',string="Plan de pago")
    payment_type = fields.Selection([('fortnight','Quincenal'),('monthly','Mensual')],string="Tipo de pago", default="fortnight")
    monthly_type = fields.Selection([('first','Primera'),('second','Segunda')],string="Quincena", default="first")
    quotes_number = fields.Integer(string="Cuotas")
    by_quotes = fields.Boolean(string="Por Cuotas")
    fixed_fee = fields.Float(string="Cuota fija")
    payment_amount = fields.Float(string="Monto Pagado", compute="get_amounts", store=True)
    pending_amount = fields.Float(string="Monto Pendiente", compute="get_amounts", store=True)

    @api.depends(
        'payslip_id',
        'payslip_id.state',
        'payment_plan_ids',
        'payment_plan_ids.state',
        'payment_plan_ids.amount',
        'by_quotes',
        'amount')
    def get_amounts(self):
        for rec in self:
            total_payment_amount = 0
            total_pending_amount = 0
            if rec.by_quotes:
                for line in rec.payment_plan_ids:
                    if line.state == 'paid':
                        total_payment_amount += line.amount

                    if line.state in ['draft','validated',False,None]:
                        total_pending_amount += line.amount
            else:
                if rec.payslip_id:
                    if rec.payslip_id.state == 'paid':
                        total_payment_amount = rec.amount
                    if rec.payslip_id.state in ['draft','validated',False,None]:
                        total_pending_amount = rec.amount
                else:
                    total_pending_amount = rec.amount
            
            rec.payment_amount = total_payment_amount
            rec.pending_amount = total_pending_amount

    @api.onchange('input_type_id')
    def _onchange_input_type_id(self):
        self.name = self.input_type_id.name

    def change_state(self):
        self.state = 'in_progress'
        if self.by_quotes:
            self.create_plan()

    def send_draft(self):
        self.state = 'draft'

    def send_cancel(self):
        self.state = 'cancel'

    @api.constrains('start_date','end_date')
    def _validate_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError('La fecha de inicio no puede ser mayor a la final')

    def finalize_deductions(self):
        deduction_ids = self.search([('state','=','in_progress')])
        if deduction_ids:
            for ded in deduction_ids:
                if not ded.by_quotes:
                    if ded.payslip_id.state == 'paid':
                        ded.write({'state':'completed'})
                        if not ded.rec_deduction_id:
                            deduction_id = ded.create_deduction(ded.start_date, ded.end_date, ded.amount, ded)
                            if deduction_id:
                                ded.rec_deduction_id = deduction_id.id
                else:
                    if ded.payment_plan_ids:
                        finalize = True
                        for plan in ded.payment_plan_ids:
                            if not plan.payslip_id:
                                finalize = False
                                break
                            else:
                                if plan.state == 'paid' and not plan.deduction_created:
                                    deduction_id = ded.create_deduction(plan.payslip_id.date_from, plan.payslip_id.date_to, plan.amount, ded)
                                    if deduction_id:
                                        plan.deduction_created = True
                                        plan.rec_deduction_id = deduction_id.id
                                        plan.payslip_id.salary_attachment_ids = [(4, deduction_id.id)]

                            if plan.state != 'paid':
                                finalize = False
                                break
                        
                        if finalize:
                            ded.write({'state':'completed'})
        return True

    def create_deduction(self, start_date, end_date, amount, deduction):
        deduction_id = self.env['hr.salary.attachment'].create({
            'employee_ids': [(4, deduction.employee_id.id)],
            'other_input_type_id': deduction.input_type_id.id,
            'date_start': start_date,
            'date_end': end_date,
            'monthly_amount': amount,
            'total_amount': amount,
            'duration_type': 'one',
            'description': deduction.name,
            'company_id': deduction.employee_id.company_id.id,
            'state': 'close',

        })
        return deduction_id

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('No se pueden eliminar registros en progreso o completados')
        res = super(otherDeductions, self).unlink()
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

        if self.fixed_fee > 0:
            quote_amount = self.fixed_fee
        else:
            if self.quotes_number == 0:
                raise ValidationError("El numero de cuotas no puede ser 0")

            quote_amount = round(self.amount / self.quotes_number, 2)
        
        
        plan = []
        
        if self.payment_type == "monthly":
            day = 1 if self.monthly_type == "first" else 16
            init_date = date(initial_date.year, initial_date.month, day)
        else:  # quincenal
            day = 1 if initial_date.day < 16 else 16
            init_date = date(initial_date.year, initial_date.month, day)

        total = 0
        for i in range(self.quotes_number):
            total += quote_amount
            self.end_date = init_date
            vals = {
                "number": i + 1,
                "amount": quote_amount,
                'other_deduction_id': self.id,
                "date": init_date
            }
            self.env['other.deductions.payment.plan'].create(vals)

            if self.payment_type == "monthly":
                # sumar un mes
                init_date = init_date + relativedelta(months=1)
                init_date = init_date.replace(day=1 if self.monthly_type == "first" else 16)
            else:  # quincenal
                if init_date.day == 1:
                    init_date = init_date.replace(day=16)
                else:
                    init_date = (init_date + relativedelta(months=1)).replace(day=1)
        self.amount = total

    def show_payroll(self):
        if self.by_quotes:
            payslip_ids = self.payment_plan_ids.mapped('payslip_id')
        else:
            payslip_ids = [self.payslip_id.id]
            
        if payslip_ids:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'list',
                'views': [(False, 'list'), (False, 'form')],
                'res_model': 'hr.payslip',
                'target': 'current',
                'domain': [('id', 'in', payslip_ids.ids)]
            }
        else:
            raise ValidationError("Aun no hay recibos de nomina creados")

    def show_deductions(self):
        if self.by_quotes:
            deduction_ids = self.payment_plan_ids.mapped('rec_deduction_id')
        else:
            deduction_ids = [sel.rec_deduction_id.id]
        
        if deduction_ids:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'list',
                'views': [(False, 'list'), (False, 'form')],
                'res_model': 'hr.salary.attachment',
                'target': 'current',
                'domain': [('id', 'in', deduction_ids.ids)]
            }
        else:
            raise ValidationError("No existen registros de deducciones")

    class otherPaymentPlanDed(models.Model):
        _name = 'other.deductions.payment.plan'
        _description = 'Plan de pago otras deducciones'

        number = fields.Integer(string="# Cuota")
        date = fields.Date(string="Fecha")
        state = fields.Selection(related='payslip_id.state',string="Estado")
        amount = fields.Float(string="Monto")
        payslip_id = fields.Many2one('hr.payslip',string="Nomina")
        other_deduction_id = fields.Many2one('hr.other.deductions',string="Otra Deduccion")
        rec_deduction_id = fields.Many2one('hr.salary.attachment',string="Rec. Deduccion")
        deduction_created = fields.Boolean(string="Deduccion creada")

        def unlink(self):
            for val in self:
                if val.state == 'paid':
                    raise ValidationError("No puede eliminar un registro pagado")
            return super().unlink()

        # @api.onchange('state')
        # def update_paid_amount(self):
        #     if self.state == 'paid':
        #         self.deduction_id.paid_amount += self.amount