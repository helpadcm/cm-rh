# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

states = [
    ('draft', 'Borrador'),
    ('required', 'Solicitado'),
    ('approved', 'Aprobado'),
    ('assigned', 'Otorgado'),
    ('pending','Por Liquidar'),
    ('finalized', 'Finalizado'),
    ('canceled', 'Cancelado')
]

class expensesRequest(models.Model):
    _name = 'cm.expenses.request'
    _description = "Solicitud de viaticos"
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "name desc"

    @api.model
    def default_get(self, fields):
        rec = super(expensesRequest, self).default_get(fields)
        user = self.env.user
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',user.id)])
        if employee_id:
            permitted_processes_ids = False
            default_process_id = False
            if employee_id.user_id:
                permitted_processes_ids = self.env['crossovered.activity'].search([('user_ids','in',employee_id.user_id.ids)])
                if len(permitted_processes_ids) == 1:
                    default_process_id = permitted_processes_ids.id

            account_number = ''
            if employee_id.sudo().bank_account_ids:
                account_number = employee_id.sudo().bank_account_ids[0].acc_number

            rec.update({
                'department_id': employee_id.department_id.id,
                'job_id': employee_id.job_id.id,
                'employee_id': employee_id.id,
                'assign_to_id': employee_id.id,
                'process_ids': permitted_processes_ids,
                'process_id': default_process_id,
                'boss_id': employee_id.parent_id.id,
                'account_number': account_number,
                'date': datetime.now().date()
            })
        return rec

    name = fields.Char(string="Nombre",default="Borrador",tracking=True,copy=False)
    employee_id = fields.Many2one('hr.employee',string="Solicitado por",tracking=True)
    job_id = fields.Many2one('hr.job',string="Puesto",tracking=True)
    department_id = fields.Many2one('hr.department',string="Departamento",tracking=True)
    purpose = fields.Char(string="Proposito del gasto",tracking=True,copy=False)
    account_number = fields.Char(string="Numero de cuenta",tracking=True)
    date = fields.Date(string="Fecha de solicitud",tracking=True)
    observations = fields.Text(string="Observaciones",tracking=True,copy=False)
    state = fields.Selection(states,string="Estado",default="draft",tracking=True,copy=False)
    boss_id = fields.Many2one('hr.employee',string="Jefe Inmediato",copy=True)
    assign_to_id = fields.Many2one('hr.employee',string="Asignado a",copy=True)

    advance_amount = fields.Float(string="Anticipo al Empleado", compute="calculate_totals")
    total_expense_amount = fields.Float(string="Total de gastos", compute="calculate_totals")
    balance_employee_amount = fields.Float(string="Saldo en Control del Empleado", compute="calculate_totals")
    infavor_employee_amount = fields.Float(string="Saldo a Favor del Empleado", compute="calculate_totals")
    refund_amount = fields.Float(string="Reembolso", copy=False)

    request_details_ids = fields.One2many('cm.expenses.request.details','request_id',string="Detalles de solicitud",copy=True)
    expenses_ids = fields.One2many('hr.expense','request_id',string="Lista de gastos") 

    need_tickets = fields.Boolean(string="Necesita boletos")
    need_transport = fields.Boolean(string="Necesita transporte")
    need_hotel = fields.Boolean(string="Necesita hotel")
    reason_expense = fields.Selection([('tour','Gira'),('training','Capacitación')],string="Motivo de gasto")
    process_id = fields.Many2one('crossovered.activity', string="Proceso")
    process_ids = fields.Many2many('crossovered.activity',string="Procesos permitidos")

    @api.depends('request_details_ids','expenses_ids','refund_amount')
    def calculate_totals(self):
        for rec in self:
            total_advance = 0
            total_expenses = 0
            if rec.request_details_ids:
                total_advance = sum(rec.request_details_ids.mapped('total_amount'))
            
            if rec.expenses_ids:
                total_expenses = sum(rec.expenses_ids.mapped('total_amount'))

            rec.advance_amount = total_advance
            rec.total_expense_amount = total_expenses

            control_employee_amount = total_advance - total_expenses
            if control_employee_amount <= 0:
                rec.balance_employee_amount = 0
            else:
                rec.balance_employee_amount = control_employee_amount - rec.refund_amount

            infavor_total = total_expenses - total_advance
            if infavor_total <= 0:
                rec.infavor_employee_amount = 0
            else:
                rec.infavor_employee_amount = infavor_total

    @api.onchange('assign_to_id')
    def get_assign_to_data(self):
        if self.assign_to_id:
            self.write({
                'department_id': self.assign_to_id.department_id.id,
                'job_id': self.assign_to_id.job_id.id,
                'boss_id': self.assign_to_id.coach_id.id,
                'account_number': self.assign_to_id.bank_account_ids.acc_number
            })

    @api.onchange('employee_id')
    def get_employee_data(self):
        permitted_processes_ids = False
        default_process_id = False
        if self.employee_id:
            if self.employee_id.user_id:
                permitted_processes_ids = self.env['crossovered.activity'].search([('user_ids','in',self.employee_id.user_id.ids)])
                if len(permitted_processes_ids) == 1:
                    default_process_id = permitted_processes_ids.id
                    self.write({
                        'process_ids': permitted_processes_ids,
                        'process_id': default_process_id,
                    })

            self.write({
                'department_id': self.employee_id.department_id.id,
                'job_id': self.employee_id.job_id.id,
                'boss_id': self.employee_id.coach_id.id,
                'account_number': self.employee_id.bank_account_ids.acc_number
            })

    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'required':
            if len(self.request_details_ids) == 0:
                raise ValidationError("Debe agregar al menos una linea en los detalles de gastos")

            if self.name == 'Borrador':
                sequence_id = self.env.ref('cm_expenses_request.expenses_request_sequence')
                if sequence_id:
                    self.name = sequence_id.next_by_id()
            self.send_email(next_state)

        if next_state == 'assigned':
            self.send_email(next_state)

        if next_state == 'approved':
            self.send_email(next_state)

        if next_state == 'pending':
            if len(self.expenses_ids) == 0:
                raise ValidationError("Debe agregar al menos un gasto")

            amount_total = 0
            for line in self.expenses_ids:
                amount_total += line.total_amount
                if line.nb_attachment == 0:
                    raise ValidationError(f"""Debe agregar comprobantes de sus gastos, el gasto {line.name} no tiene adjuntos.""")

            if amount_total == 0:
                raise ValidationError("El total de gastos no puede ser 0, por favor revise los gastos agregados.")
                
            self.create_report_expenses()
            self.send_email(next_state)

        self.state = next_state

    def send_email(self, state):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if state == 'required':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = self.boss_id.name
            email_to = self.boss_id.user_id.login
            message_txt = f"""El colaborador {self.assign_to_id.name} ha creado una solicitud de viaticos que necesita de su aprobación"""
            subject = 'Solicitud de viaticos'

        if state == 'approved':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = 'EDUARDO SEVILLA COELLO'
            email_to = 'esevilla@cmairlines.com,contabilidad@cmairlines.com'
            message_txt = f"""El colaborador {self.assign_to_id.name} ha creado una solicitud de viaticos que necesita de su aprobación"""
            subject = 'Solicitud de viaticos'

        if state == 'assigned':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = self.assign_to_id.name
            email_to = self.assign_to_id.user_id.login
            message_txt = f"""Su solicitud de viaticos ha sido asignada a su cuenta. Recuerde que tiene 3 dias habiles despues de su fecha de regreso para realizar su liquidación a travez de odoo"""
            subject = 'Asignación de viaticos'

        if state == 'pending':
            for_user = self.assign_to_id.expense_manager_id.name
            email_to = self.assign_to_id.expense_manager_id.login
            message_txt = f"""Se ha creado un reporte de gastos del empleado {self.assign_to_id.name} para su revisión."""
            subject = 'Reporte de gastos creado'

            expense_sheet_id = self.env['expenses.sheet.request'].search([('request_id','=',self.id)])
            base_url += '/web#id=%d&view_type=form&model=%s' % (expense_sheet_id.id, expense_sheet_id._name)
        
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
                                                        <span style="font-size: 10px;color:black"><h2>Solicitud de aprobación de viaticos</h2></span><br/>
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
                                                                    style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;">Ver registro</a>
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

    def create_report_expenses(self):
        # expense_sheet_id = self.env['hr.expense.sheet'].search([('request_id','=',self.id)])
        # if expense_sheet_id:
        #     expense_sheet_id.unlink()
        
        # self.expenses_ids.action_submit_expenses()
        expense_sheet_id = self.env['expenses.sheet.request'].search([('request_id','=',self.id)])
        if expense_sheet_id:
            expense_sheet_id.unlink()

        sheet_obj = self.env['expenses.sheet.request']
        sequence_id = self.env.ref('cm_expenses_request.expenses_sheet_request_sequence')
        vals = {
            'employee_id': self.assign_to_id.id,
            'user_id': self.assign_to_id.expense_manager_id.id,
            'request_id': self.id,
            'name': f"""Liq. de viaticos {self.assign_to_id.name}""",
            'state': 'sent',
            'number': sequence_id.next_by_id()
        }
        sheet_id = sheet_obj.create(vals)
        self.expenses_ids.write({'expense_sheet_req_id': sheet_id.id, 'state': 'submitted'})
        

    def show_expenses_report(self):
        expense_sheet_id = self.env['expenses.sheet.request'].search([('request_id','=',self.id)])
        if expense_sheet_id:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'expenses.sheet.request',
                'target': 'current',
                'res_id': expense_sheet_id.id
            }

    def show_expenses_debit(self):
        debit_id = self.env['debit.credit'].search([('request_id','=',self.id)])
        if debit_id:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'debit.credit',
                'target': 'current',
                'res_id': debit_id.id
            }

    def show_expenses_deposit(self):
        deposit_id = self.env['banks.deposit'].search([('request_id','=',self.id)])
        if deposit_id:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'banks.deposit',
                'target': 'current',
                'res_id': deposit_id.id
            }

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("Solo puede borrar solicitudes en estado borrador")
        return super(expensesRequest, self).unlink()	

class expensesRequestDetails(models.Model):
    _name = 'cm.expenses.request.details'
    _description = "Detalles Solicitud de viaticos"

    request_id = fields.Many2one('cm.expenses.request',string="Solicitud")
    job_id = fields.Many2one('hr.job',string="Puesto")
    date = fields.Date(string="Fecha")
    breakfast_cti_id = fields.Many2one('cargo.airport',string="Desayuno")
    lunch_cti_id = fields.Many2one('cargo.airport',string="Almuerzo")
    dinner_cti_id = fields.Many2one('cargo.airport',string="Cena")
    breakfast_amount = fields.Float(string="Monto Desayuno")
    lunch_amount = fields.Float(string="Monto Almuerzo")
    dinner_amount = fields.Float(string="Monto Cena")

    transport_amount = fields.Float(string="Transporte")
    tax_amount = fields.Float(string="Impuestos")
    parking_amount = fields.Float(string="Parqueo")
    purchase_amount = fields.Float(string="Compras")
    others_amount = fields.Float(string="Otros")
    total_amount = fields.Float(string="TOTAL")
    
    @api.onchange('breakfast_amount','lunch_amount','dinner_amount','transport_amount','tax_amount','parking_amount','purchase_amount','others_amount')
    def get_total_day(self):
        self.total_amount = self.breakfast_amount + self.lunch_amount + self.dinner_amount + self.transport_amount + self.tax_amount + self.parking_amount + self.purchase_amount + self.others_amount

    @api.onchange('breakfast_cti_id')
    def get_breakfast_amount(self):
        if self.breakfast_cti_id:
            conf_ids = self.env['conf.expenses.request'].search([])
            for conf in conf_ids:
                conf_job_id = conf.job_ids.filtered(lambda job: job.id == self.job_id.id)
                if conf_job_id:
                    for line in conf.details_expenses_ids:
                        if self.breakfast_cti_id.id in line.ctis_ids.ids:
                            self.breakfast_amount = line.breakfast_amount
                            break

    @api.onchange('lunch_cti_id')
    def get_lunch_amount(self):
        if self.lunch_cti_id:
            conf_ids = self.env['conf.expenses.request'].search([])
            for conf in conf_ids:
                conf_job_id = conf.job_ids.filtered(lambda job: job.id == self.job_id.id)
                if conf_job_id:
                    for line in conf.details_expenses_ids:
                        if self.lunch_cti_id.id in line.ctis_ids.ids:
                            self.lunch_amount = line.lunch_amount
                            break

    @api.onchange('dinner_cti_id')
    def get_dinner_amount(self):
        if self.dinner_cti_id:
            conf_ids = self.env['conf.expenses.request'].search([])
            for conf in conf_ids:
                conf_job_id = conf.job_ids.filtered(lambda job: job.id == self.job_id.id)
                if conf_job_id:
                    for line in conf.details_expenses_ids:
                        if self.dinner_cti_id.id in line.ctis_ids.ids:
                            self.dinner_amount = line.dinner_amount
                            break