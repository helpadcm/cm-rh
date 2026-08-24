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
    ('pending','Liquidacion Conforme'),
    ('exception','Liquidacion Excepcional'),
    ('legal','Legal'),
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
            edit = False
            if employee_id.sudo().bank_account_ids:
                account_number = employee_id.sudo().bank_account_ids[0].acc_number

            if self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
                edit = True

            if not employee_id.expense_approver_id:
                raise ValidationError("No se ha definido un aprobador de viáticos para el colaborador %s, por favor contacte a su administrador de odoo" % (employee_id.name))

            allow_employee_ids = self.env['hr.employee'].search([('expense_approver_id','=',employee_id.id)])
            if self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
                allow_employee_ids = self.env['hr.employee'].search([])

            rec.update({
                'department_id': employee_id.department_id.id,
                'job_id': employee_id.job_id.id,
                'employee_id': employee_id.id,
                'assign_to_id': employee_id.id,
                'process_ids': permitted_processes_ids,
                'process_id': default_process_id,
                'boss_id': employee_id.expense_approver_id.id,
                'account_number': account_number,
                'date': datetime.now().date(),
                'edit_employee': edit,
                'allow_employee_ids': allow_employee_ids
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
    assign_to_id = fields.Many2one('hr.employee',string="Asignado a",copy=True,tracking=True)
    allow_employee_ids = fields.Many2many('hr.employee',string="Empleados a cargo",copy=True,tracking=True)

    advance_amount = fields.Float(string="Anticipo al Empleado", compute="calculate_totals")
    total_expense_amount = fields.Float(string="Total de gastos", compute="calculate_totals")
    balance_employee_amount = fields.Float(string="Saldo en Control del Empleado", compute="calculate_totals")
    infavor_employee_amount = fields.Float(string="Saldo a Favor del Empleado", compute="calculate_totals")
    refund_amount = fields.Float(string="Reembolso", copy=False)

    request_details_ids = fields.One2many('cm.expenses.request.details','request_id',string="Detalles de solicitud",copy=True)
    expenses_ids = fields.One2many('hr.expense','request_id',string="Lista de gastos")

    need_tickets = fields.Boolean(string="Necesita boletos",tracking=True)
    need_transport = fields.Boolean(string="Necesita transporte",tracking=True)
    need_hotel = fields.Boolean(string="Necesita hotel",tracking=True)
    hotel_specifications = fields.Text(string="Especificaciones de hotel",tracking=True)
    reason_expense = fields.Selection([('tour','Gira'),('training','Capacitación')],string="Motivo de gasto",tracking=True)
    process_id = fields.Many2one('crossovered.activity', string="Proceso",tracking=True)
    process_ids = fields.Many2many('crossovered.activity',string="Procesos permitidos")
    limit_date = fields.Date(string="Fecha limite de liquidacion",compute="_calculate_limit_date")
    omit_settlement = fields.Boolean(string="Omitir liquidacion")
    edit_employee = fields.Boolean(string="Editar Empleado")
    refund_state = fields.Selection([('na','No Aplica'),('without_refund','Sin Reembolsar'),('refunded','Reembolsado')],string="Estado de Reembolso",default="na",tracking=True)
    refund_done = fields.Boolean(string="Reembolso realizado",copy=False)

    exeption_id = fields.Many2one('expense.exceptional.reason',string='Motivo de Excepcion',copy=False,tracking=True)
    description = fields.Text(string="Motivo",copy=False,tracking=True)

    tickets_request_ids = fields.One2many('cm.expenses.request.ticket','expense_request_id',string="Solicitud de boletos")
    quote_amount_tickets = fields.Float(string="Cotizacion Boletos",compute="calculate_totals")
    ctis_hotels_ids = fields.Many2many('cargo.airport',string="Reservar hotel en:")

    def refunded_balance(self):
        if self.refund_state == 'without_refund':
            self.refund_state = 'refunded'
            self.refund_done = True

    @api.onchange('infavor_employee_amount','refund_done','exeption_id')
    def _onchange_infavor_employee_amount(self):
        if not self.refund_done:
            if self.infavor_employee_amount > 0:
                if self.exeption_id.skip_exception:
                    self.refund_state = 'na'
                else:
                    self.refund_state = 'without_refund'
            else:
                self.refund_state = 'na'
        else:
            self.refund_state = 'refunded'

    @api.depends('request_details_ids')
    def _calculate_limit_date(self):
        for rec in self:
            rec.limit_date = False
            if rec.request_details_ids:
                last_line_id = rec.request_details_ids[-1]
                if last_line_id:
                    current_date = last_line_id.date
                    days_added = 0

                    while days_added < 5:
                        current_date += timedelta(days=1)

                        # Lunes=0 ... Viernes=4
                        if current_date.weekday() < 5:
                            days_added += 1
                    rec.limit_date = current_date

    @api.depends('request_details_ids','expenses_ids','refund_amount','tickets_request_ids')
    def calculate_totals(self):
        for rec in self:
            total_advance = 0
            total_expenses = 0
            total_tickets_amount = 0
            if rec.request_details_ids:
                total_advance = sum(rec.request_details_ids.mapped('total_amount'))

            if rec.tickets_request_ids:
                total_tickets_amount = sum(rec.tickets_request_ids.mapped('quote_amount'))
                total_advance += total_tickets_amount
            
            if rec.expenses_ids:
                total_expenses = sum(rec.expenses_ids.mapped('total_amount'))

            rec.advance_amount = total_advance
            rec.total_expense_amount = total_expenses
            rec.quote_amount_tickets = total_tickets_amount

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
            if not self.assign_to_id.expense_approver_id:
                raise ValidationError("No se ha definido un aprobador de viáticos para el colaborador %s, por favor contacte a su administrador de odoo" % (self.assign_to_id.name))

            self.write({
                'department_id': self.assign_to_id.department_id.id,
                'job_id': self.assign_to_id.job_id.id,
                'boss_id': self.assign_to_id.expense_approver_id.id,
                'account_number': self.assign_to_id.bank_account_ids.acc_number
            })

    @api.onchange('employee_id')
    def get_employee_data(self):
        permitted_processes_ids = False
        default_process_id = False
        if self.employee_id:
            if self.employee_id.user_id:
                permitted_processes_ids = self.env['crossovered.activity'].search([('user_ids','in',self.employee_id.user_id.ids)])
                allow_employee_ids = self.env['hr.employee'].search([('expense_approver_id','=',self.employee_id.id)])
                if self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
                    allow_employee_ids = self.env['hr.employee'].search([])

                if len(permitted_processes_ids) == 1:
                    default_process_id = permitted_processes_ids.id
                    self.write({
                        'process_ids': permitted_processes_ids,
                        'process_id': default_process_id,
                        'allow_employee_ids': allow_employee_ids
                    })
                    
    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'required':
            if len(self.request_details_ids) == 0:
                raise ValidationError("Debe agregar al menos una linea en los detalles de gastos")

            if self.need_tickets: 
                if len(self.tickets_request_ids) == 0:
                    raise ValidationError("Si necesita boletos, debe ingresar los datos para solicitud de boletos")

                for line in self.tickets_request_ids:
                    if not line.passport_file:
                        raise ValidationError("Debe agregar fotocopia de su identidad o pasaporte en su solicitud de boletos aereos.")
                

            if self.name == 'Borrador':
                sequence_id = self.env.ref('cm_expenses_request.expenses_request_sequence')
                if sequence_id:
                    self.name = sequence_id.next_by_id()
            
            if self.boss_id.id == self.employee_id.id:
                next_state = 'approved'
            else:
                self.send_email(next_state)

        if next_state in ['assigned','exception','approved']:
            if not self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
                if self.boss_id.user_id.id != self.env.user.id and next_state == 'approved':
                    raise ValidationError("Solo el aprobador de viaticos para este empleado puede aprobar en esta solicitud")

            if next_state == 'approved':
                if self.need_hotel:
                    self.send_email_hotel()
                if self.need_tickets:
                    self.create_ticket_request()

            self.send_email(next_state)

        if next_state == 'pending':
            with_exception = False
            if not self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
                if self.assign_to_id.user_id.id != self.env.user.id:
                    raise ValidationError("Solo el empleado asignado a la solicitud puede enviar a liquidar")

            if len(self.expenses_ids) == 0 and self.balance_employee_amount > 0:
                raise ValidationError("Debe agregar al menos un gasto")

            if self.exeption_id and self.exeption_id.skip_exception:
                with_exception = 'according'

            amount_total = 0
            for line in self.expenses_ids:
                amount_total += line.total_amount
                if line.nb_attachment == 0:
                    raise ValidationError(f"""Debe agregar comprobantes de sus gastos, el gasto {line.name} no tiene adjuntos.""")

            if amount_total == 0 and self.balance_employee_amount > 0:
                raise ValidationError("El total de gastos no puede ser 0, por favor revise los gastos agregados.")

            if self.balance_employee_amount > 0:
                raise ValidationError("No puede enviar a liquidar, aun tiene saldo en control del empleado que debe ser tratado")
                
            self.create_report_expenses(with_exception)
            self.send_email(next_state)

        self.state = next_state

    def send_email_hotel(self):
        ctis_name = ''
        if self.ctis_hotels_ids:
            ctis_name = ', '.join([cti.ref for cti in self.ctis_hotels_ids])

        mail = self.env['mail.mail'].sudo().create({
            'subject': f"Solicitud de hotel creada por {self.assign_to_id.name} en las estaciones {ctis_name} mediante solicitud de viaticos {self.name}",
            'body_html': f"""<p>El empleado {self.assign_to_id.name} solicita la reservacion de hotel por motivos de {self.purpose} con las siguientes especificaciones: </p></br>
                        {self.hotel_specifications}""",
            'email_from': self.assign_to_id.user_id.login,
            'email_to': 'esevilla@cmairlines.com',
            'email_cc': 'rosa@cmairlines.com',
        })
        mail.send()

    def create_ticket_request(self):
        program_id = self.env['cm.ticket.request.program'].search([('code','=','VIAT')])
        for line in self.tickets_request_ids:
            if line.ticket_type_request == 'internal':
                vals = {
                    'airline_id': line.airline_id.id,
                    'program_id': program_id.id,
                    'program_code': program_id.zenith_code,
                    'user_id': self.assign_to_id.user_id.id,
                    'boss_id': self.boss_id.id,
                    'request_type': line.request_type
                }

                req_ticket_id = self.env['cm.ticket.request'].create(vals)
                line.list_routes_ids.write({'request_id': req_ticket_id.id})

                attachment_id = False
                attachment_name = False
                if line.passport_file:
                    attachment_id = line.passport_file
                    attachment_name = line.passport_file_name
                else:
                    attachment_id = self.assign_to_id.id_card
                    attachment_name = f'Id/Pasaporte {self.assign_to_id.name}'

                if not attachment_id:
                    raise ValidationError("Debe agregar fotocopia de su identidad o pasaporte en su solicitud de boletos aereos.")

                passenge_id = self.env['cm.ticket.request.line'].create({
                    'employee_id': self.assign_to_id.id,
                    'passenger_type': 'internal',
                    'request_id': req_ticket_id.id,
                    'more_luggage': line.more_luggage,
                    'id_file': attachment_id,
                    'id_file_name': attachment_name,
                    'class_name': 'noRev',
                    'description': self.purpose
                })
                
                line.request_ticket_id = req_ticket_id.id
                passenge_id.get_data()
                req_ticket_id.with_context({'state':'send'}).change_state()

    def send_email(self, state):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        show_button = True
        title = f"<h2>Solicitud de aprobación de viaticos</h2>"
        if state == 'required':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = self.boss_id.name
            email_to = self.boss_id.user_id.login
            message_txt = f"""El colaborador {self.assign_to_id.name} ha creado una solicitud de viaticos que necesita de su aprobación"""
            subject = 'Solicitud de viaticos'

        if state == 'exception':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = self.boss_id.name
            email_to = self.boss_id.user_id.login
            message_txt = f"""El colaborador {self.assign_to_id.name} ha solicituado una exepcion en su liquidacion de viaticos que necesita de su aprobación"""
            subject = 'Solicitud de viaticos motivo exepcional'
            title = f"<h2>Solicitud de reembolso de viaticos</h2>"

            mail = self.env['mail.mail'].sudo().create({
                'subject': "Liquidacion excepcional",
                'body_html': f"""<p>Su liquidacion de viaticos se encuentra en el estado de liquidacion excepcional, comuniquese con su jefe inmediato para poder resolver su liquidacion con monto gastado superior al asignado</p>""",
                'email_to': self.assign_to_id.user_id.login,
            })
            mail.send()

        if state == 'approved':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = 'EDUARDO SEVILLA COELLO'
            email_to = 'esevilla@cmairlines.com,contabilidad@cmairlines.com'
            message_txt = f"""El colaborador {self.assign_to_id.name} ha creado una solicitud de viaticos que necesita de su aprobación"""
            subject = 'Solicitud de viaticos'

        if state == 'refund':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = 'EDUARDO SEVILLA COELLO'
            email_to = 'esevilla@cmairlines.com'
            message_txt = f"""{self.boss_id.name} ha aprobado un reembolso para el empleado {self.assign_to_id.name} de la solicitud de viaticos {self.name}."""
            subject = 'Reembolso de viaticos'
            title = f"<h2>Reembolso Aprobado</h2>"

        if state == 'assigned':
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            for_user = self.assign_to_id.name
            email_to = self.assign_to_id.user_id.login
            message_txt = f"""Su solicitud de viaticos ha sido asignada a su cuenta. Recuerde que tiene 3 dias habiles despues de su fecha de regreso para realizar su liquidación a travez de odoo, debera hacer entrega de sus comprobantes de gastos o depositos realizados por dinero sobrante de manera fisica al area de finanzas."""
            subject = 'Asignación de viaticos'
            title = f"<h2>Asignación de viaticos</h2>"
            show_button = False

        if state == 'pending':
            for_user = self.assign_to_id.expense_manager_id.name
            email_to = self.assign_to_id.expense_manager_id.login
            message_txt = f"""Se ha creado un reporte de gastos del empleado {self.assign_to_id.name} para su revisión."""
            subject = 'Reporte de gastos creado'
            title = "<h2>Reporte de gastos creado</h2>"

            expense_sheet_id = self.env['expenses.sheet.request'].search([('request_id','=',self.id)])
            base_url += '/web#id=%d&view_type=form&model=%s' % (expense_sheet_id.id, expense_sheet_id._name)

        button_html = ""
        if show_button:
            button_html = f"""
            <div style="margin: 16px 0px 16px 0px;">
                <a href="{base_url}"
                    style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;">Ver registro</a>
            </div>
            """
        
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
                                                        <span style="font-size: 10px;color:black">{title}</span><br/>
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
                                                            {show_button_html}
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
        """.format(title=title,for_user=for_user,message=message_txt,url=base_url,show_button_html=button_html)

        mail_values = {
            'body_html': body,
            'email_to': email_to,
            'subject': subject,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

    def create_report_expenses(self, with_exception=False):
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

        if with_exception:
            if self.exeption_id.skip_exception:
                vals['exception_solution'] = 'according'
            else:
                vals['exception_solution'] = with_exception
                
            vals['exeption_id'] = self.exeption_id.id
            vals['description'] = self.description or self.exeption_id.name

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
        deposit_ids = self.env['banks.deposit'].search([('request_id','=',self.id),('state','=','validated')])
        self.ensure_one()
        if len(deposit_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'banks.deposit',
                'target': 'current',
                'res_id': deposit_ids.id
            }
        if len(deposit_ids) > 1:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'list',
                'views': [(False, 'list'), (False, 'form')],
                'res_model': 'banks.deposit',
                'target': 'current',
                'domain': [('id', 'in', deposit_ids.ids)]
            }

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("Solo puede borrar solicitudes en estado borrador")
        return super(expensesRequest, self).unlink()

    def approve_exception(self):
        if not self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
            if self.boss_id.user_id.id != self.env.user.id:
                raise ValidationError("Solo el aprobador de viaticos para este empleado puede aprobar en esta solicitud")
        self.write({'state':'finalized', 'refund_state': 'without_refund'})
        self.send_email('refund')
        self.create_report_expenses(with_exception='exception')

    def reject_exception(self):
        if not self.env.user.has_group("cm_expenses_request.group_expenses_request_manager"):
            if self.boss_id.user_id.id != self.env.user.id:
                raise ValidationError("Solo el aprobador de viaticos para este empleado puede rechazar esta solicitud")
        self.write({'state':'finalized', 'refund_state': 'na'})
        self.create_report_expenses(with_exception='rejected')

    def cron_review_deadline(self):
        pending_expenses_ids = self.search([('state','=','assigned')])
        actual_date = (datetime.now() - timedelta(hours=6)).date()
        for exp in pending_expenses_ids:
            expense_sheet_id = self.env['expenses.sheet.request'].search([('request_id','=',exp.id)])
            if actual_date > exp.limit_date and not expense_sheet_id:
                for_user = exp.assign_to_id.name
                email_to = 'legalrh@cmairlines.com'
                message_txt = f"""El empleado {for_user} no ha realizado su liquidacion de viaticos con fecha limite {exp.limit_date.strftime('%d/%m/%Y')}."""
                subject = f'Liquidacion de viaticos no realizada'
                
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
                                                                <span style="font-size: 10px;color:black"><h2>Liquidacion de viaticos no realizada</h2></span><br/>
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
                                                                    {message}
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
                """.format(message=message_txt)

                mail_values = {
                    'body_html': body,
                    'email_to': email_to,
                    'subject': subject,
                }
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()
            

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