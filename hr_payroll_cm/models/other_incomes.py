from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

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
    state = fields.Selection([('draft','Borrador'),('in_progress','En proceso'),('completed','Completado')],string="Estado",default="draft", tracking=True)

    def change_state(self):
        self.state = 'in_progress'

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
                if income.end_date < datetime.now().date():
                    income.write({'state':'completed'})
        return True

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('No se pueden eliminar registros en progreso o completados')
        res = super(otherIncomes, self).unlink()
        return res