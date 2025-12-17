# -*- coding: utf-8 -*-
import calendar
import math
from odoo.http import request
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta, time

state_list = [('draft','Borrador'),('pending','Pendiente de aprobar'),('approved','Aprobado por Jefe'),('assessment','En Evaluacion'),('waiting','En Espera'),('finance','Finanzas'),('payroll','Asignar a Nomina'),('finalized','Finalizado'),('cancel','Rechazado')]
fees_list = [('1','1 Mes'),('2','2 Meses'),('3','3 Meses'),('4','4 Meses'),('5','5 Meses'),('6','6 Meses'),('7','7 Meses'),('8','8 Meses'),('9','9 Meses'),('10','10 Meses'),('11','11 Meses'),('12','12 Meses')]

class requestLoan(models.Model):    
    _name = 'rrhh.request.loan'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Solicitud de prestamo interno"
    _order = "name asc"

    @api.model
    def default_date(self):
        return datetime.now().date()

    name = fields.Char(string="Numero",default="Borrador",tracking=True,copy=False)
    employee_id = fields.Many2one('hr.employee',string="Empleado",tracking=True)
    boss_id = fields.Many2one('hr.employee',string="Jefe Inmediato")
    seniority = fields.Char(string="Antiguedad")
    start_date = fields.Date(string="Fecha de Ingreso")
    date = fields.Date(string="Fecha",default=default_date)
    reason = fields.Text(string="Asunto",tracking=True)
    amount = fields.Integer(string="Monto a Solicitar",tracking=True)
    monthly_amount = fields.Float(string="Monto Mensual",tracking=True)
    fortnight_amount = fields.Float(string="Monto Quincenal",tracking=True)
    fees = fields.Selection(fees_list,string="Cuotas",tracking=True)
    state = fields.Selection(state_list, string="Estado",default="draft",tracking=True)
    initial_deduction_date = fields.Date(string="Inicio de Deduccion")
    payment_id = fields.Many2one('mcheck.mcheck',string="Pago")
    deduction_id = fields.Many2one('hr.salary.attachment',string="Deduccion")
    estimated_date = fields.Date(string="Fecha estimada")

    @api.onchange('employee_id')
    def get_employee_data(self):
        if self.employee_id:
            self.write({
                'seniority': self.employee_id.seniority,
                'start_date': self.employee_id.date_start_contract,
                'boss_id': self.employee_id.department_id.request_approve_id.id
            })

    @api.onchange('fees','amount','start_date')
    def calculate_amounts(self):
        if self.fees and self.amount > 0:
            days = (datetime.now().date() - self.start_date).days
            years = math.ceil(days/365)

            max_amount = 0
            if years == 1:
                max_amount = 12000
            elif years in [2,3]:
                max_amount = 15000
            elif years > 3:
                max_amount = 18000

            if self.amount > max_amount:
                raise ValidationError(f"""El monto maximo que puede solicitar es {max_amount}""")

            self.monthly_amount = self.amount / int(self.fees)
            self.fortnight_amount = self.monthly_amount / 2

    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'pending':
            if self.name == 'Borrador':
                sequence_id = self.env.ref('cm_rrhh_management.request_loan_sequence')
                if sequence_id:
                    self.name = sequence_id.next_by_id()

        if next_state == 'pending':
            self.send_email(next_state)
        elif next_state == 'approved':
            self.send_email(next_state)
        elif next_state == 'finance':
            self.send_email(next_state)
        elif next_state == 'payroll':
            self.create_payment()
            self.send_email(next_state)

        self.state = next_state

    def send_email(self, state):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        if state == 'pending':
            for_user = self.boss_id.name
            email_to = self.boss_id.user_id.login
            message_txt = f"""El colaborador {self.employee_id.name} ha creado una solicitud de prestamo interno que necesita de su aprobación"""
            subject = 'Solicitud de prestamo'
        elif state == 'approved':
            notify_employee_id = self.env['hr.employee'].search([('role_in_loans','=','evaluator_rrhh')])
            for_user = notify_employee_id.name
            email_to = notify_employee_id.user_id.login
            message_txt = f"""Ha sido aprobada la solicitud de prestamo del colaborador {self.employee_id.name} que necesita de evaluación."""
            subject = 'Solicitud de prestamo aprobada'
        elif state == 'finance':
            notify_employee_id = self.env['hr.employee'].search([('role_in_loans','=','evaluator_finance')])
            for_user = notify_employee_id.name
            email_to = notify_employee_id.user_id.login
            message_txt = f"""La solicitud del colaborador {self.employee_id.name} ya ha sido evaluada y necesita de su aprobación."""
            subject = 'Solicitud de prestamo evaluada'
        elif state == 'payroll':
            notify_employee_id = self.env['hr.employee'].search([('role_in_loans','=','check_creator')])
            for_user = notify_employee_id.name
            email_to = notify_employee_id.user_id.login
            message_txt = f"""Se ha probado la solicitud de prestamo del colaborador {self.employee_id.name} y se ha generado el pago en estado borrador para la emision del cheque."""
            subject = 'Emision de cheque por prestamo interno'
        
        body = """
            <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
                    <tr>
                        <td align="center">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; border-collapse:separate;">
                                <tbody>
                                    <!-- HEADER -->
                                    <tr>
                                        <td align="center" style="min-width: 590px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                <tr>
                                                    <td valign="middle" style="font-size: 10px;color:black">
                                                        <span style="font-size: 10px;color:black"><h2>Solicitud de Prestamo Interno</h2></span><br/>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td colspan="2" style="text-align:center;">
                                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- CONTENT -->
                                    <tr>
                                        <td align="center" style="min-width: 590px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                <tr>
                                                    <td valign="top" style="font-size: 13px;">
                                                        <div>
                                                            <p>Estimado(a) {for_user},</p>

                                                            {message}
                                                            <div style="margin: 16px 0px 16px 0px;">
                                                                <a href="{url}"
                                                                    style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;">Ver solicitud</a>
                                                            </div>
                                                            <br/>Saludos<br/>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="text-align:center;">
                                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </table>
        """.format(for_user=for_user,message=message_txt,url=base_url)

        mail_values = {
            'body_html': body,
            'email_to': email_to,
            'subject': subject,
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def create_payment(self):
        journal_id = self.env['account.journal'].search([('code','=','BPLPS')])
        vals = {
            'journal_id': journal_id.id,
            'date': datetime.now() - timedelta(hours=6),
            'doc_type': 'transference',
            'total': self.amount,
            'reference': self.employee_id.name,
            'name': f"""Prestamo interno a nombre de {self.employee_id.name} ({int(self.fees) * 2} cuotas)"""
        }
        payment = self.env['mcheck.mcheck'].create(vals)
        account_id = self.env['account.account'].search([('code','=','105.01')])
        line_values = {
            'account_id': account_id.id,
            'mcheck_id': payment.id,
            'name': 'Prestamo Interno',
            'amount': self.amount,
            'type': 'dr',
            'chqmanalitics': self.employee_id.analytic_account_id.id or False,
        }
        self.env['mcheck.mcheck_name'].create(line_values)
        self.payment_id = payment.id

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("Solo puede borrar solicitudes en estado borrador")
        return super(requestLoan, self).unlink()

    def create_deduction(self):
        deduction_type_id = self.env['hr.salary.attachment.type'].search([('code','=','INTLOAN')])
        vals = {
            'employee_ids': [(4, self.employee_id.id)],
            'description': 'Prestamo Interno',
            'deduction_type_id': deduction_type_id.id,
            'date_start': self.initial_deduction_date,
            'total_amount': self.amount,
            'monthly_amount': self.monthly_amount,
            'by_quotes': True,
            'payment_type': 'fortnight',
            'quotes_number': int(self.fees) * 2
        }

        ded_id = self.env['hr.salary.attachment'].create(vals)
        ded_id.create_plan()
        self.deduction_id = ded_id.id

    def print_receipt(self):
        datas = {'request_id': self.id}
        return self.env.ref('cm_rrhh_management.receipt_deduction_action').report_action(self, data = datas)

    def show_payment(self):
        if self.payment_id:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'mcheck.mcheck',
                'target': 'current',
                'res_id': self.payment_id.id
            }