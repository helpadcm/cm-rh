from odoo import fields, models, api, _
from odoo.http import request
from odoo.tools.misc import format_date
from odoo.exceptions import AccessError, UserError, ValidationError

class HrLeavesType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string="Codigo")
    code_zenith = fields.Char(string="Codigo Zenith")

class HrLeavesInh(models.Model):
    _inherit = 'hr.leave'
    
    tickets_request = fields.Integer(string="Boletos Solicitados", tracking=True)
    code = fields.Char(related="holiday_status_id.code",string="Codigo")
    exit_route_id = fields.Many2one('flight.routes',string="Ruta de Salida", tracking=True)
    return_route_id = fields.Many2one('flight.routes',string="Ruta de Regreso", tracking=True)
    exit_only = fields.Boolean(string="Solo Salida",tracking=True)
    open_back = fields.Boolean(string="Regreso Abierto",tracking=True)
    beneficiary1 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 1", tracking=True)
    beneficiary2 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 2", tracking=True)
    beneficiary3 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 3", tracking=True)
    beneficiary4 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 4", tracking=True)
    beneficiary5 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 5", tracking=True)
    beneficiary6 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 6", tracking=True)
    beneficiary7 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 7", tracking=True)
    beneficiary8 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 8", tracking=True)
    beneficiary9 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 9", tracking=True)
    char_date_from = fields.Char(string="Fecha inicial string")
    char_date_to = fields.Char(string="Fecha final string")
    # return_route_open = fields.Char(string="Ruta regreso Open", compute="get_return_open_route")

    @api.constrains('tickets_request')
    def _check_tickets_request(self):
        for record in self:
            if record.tickets_request > 9:   # 🔹 Máximo permitido
                raise ValidationError("No puede solicitar mas de 9 boletos.")
            if record.tickets_request < 0:     # 🔹 Mínimo permitido (opcional)
                raise ValidationError("El valor no puede ser negativo.")

    def _get_leaves_on_public_holiday(self):
        if self.code not in ['PFLY','SCP','SCSE']:
            res = super(HrLeavesInh, self)._get_leaves_on_public_holiday()
            return res
        else:
            return False


    def action_approve(self, check_state=True):
        res = super(HrLeavesInh, self).action_approve(check_state)
        if self.holiday_status_id.code == 'VAC':
            if len(self.employee_id.vacation_details_ids) > 0:
                if len(self.employee_id.vacation_details_ids) == 1:
                    pending_days_1 = self.employee_id.vacation_details_ids[0].pending_days
                    difference_1 = pending_days_1 - self.number_of_days
                    if difference_1 < 0:
                        self.employee_id.vacation_details_ids[0].pending_days = 0
                        self.employee_id.early_vacations += abs(difference_1)
                    else:
                        self.employee_id.vacation_details_ids[0].pending_days -= self.number_of_days
                else:
                    pending_days_1 = self.employee_id.vacation_details_ids[0].pending_days
                    difference_1 = pending_days_1 - self.number_of_days
                    if difference_1 < 0:
                        self.employee_id.vacation_details_ids[0].pending_days = 0
                        pending_days_2 = self.employee_id.vacation_details_ids[1].pending_days
                        difference_2 = pending_days_2 - abs(difference_1)
                        if difference_2 < 0:
                            self.employee_id.vacation_details_ids[1].pending_days = 0
                            self.employee_id.early_vacations += abs(difference_2)
                        else:
                            self.employee_id.vacation_details_ids[1].pending_days -= abs(difference_1)
                    else:
                        self.employee_id.vacation_details_ids[0].pending_days -= self.number_of_days
            else:
                self.employee_id.early_vacations += self.number_of_days
        elif self.holiday_status_id.code == 'HCOMP':
            if self.request_unit_half:
                hours_taken = 4
            else:
                hours_taken = self.number_of_days * 8
            self.employee_id.compensatory_hours -= hours_taken
        elif self.holiday_status_id.code in ['PFLY','SCP','SCSE']:
            self.validate_beneficiaries()
            if self.holiday_status_id.code == 'PFLY':
                    
                if self.company_id.id == 1:
                    if self.tickets_request > self.employee_id.program_to_fly:
                        raise ValidationError(f"""Los boletos disponibles para el empleado {self.employee_id.name} es de {self.employee_id.program_to_fly}""")

                    if self.exit_only:
                        self.employee_id.program_to_fly -= (self.tickets_request/2)
                    else:
                        self.employee_id.program_to_fly -= self.tickets_request
            self.send_email()
        return res

    def validate_beneficiaries(self):
        if self.tickets_request == 0:
            raise ValidationError("La cantidad solicitada debe ser mayor que 0")

        tickets = []
        if int(self.tickets_request) == 1:
            tickets.append(int(self.beneficiary1.id))
        elif int(self.tickets_request) == 2:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
        elif int(self.tickets_request) == 3:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
        elif int(self.tickets_request) == 4:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
        elif int(self.tickets_request) == 5:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
            tickets.append(int(self.beneficiary5.id))
        elif int(self.tickets_request) == 6:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
            tickets.append(int(self.beneficiary5.id))
            tickets.append(int(self.beneficiary6.id))
        elif int(self.tickets_request) == 7:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
            tickets.append(int(self.beneficiary5.id))
            tickets.append(int(self.beneficiary6.id))
            tickets.append(int(self.beneficiary7.id))
        elif int(self.tickets_request) == 8:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
            tickets.append(int(self.beneficiary5.id))
            tickets.append(int(self.beneficiary6.id))
            tickets.append(int(self.beneficiary7.id))
            tickets.append(int(self.beneficiary8.id))
        elif int(tickets_request) == 9:
            tickets.append(int(self.beneficiary1.id))
            tickets.append(int(self.beneficiary2.id))
            tickets.append(int(self.beneficiary3.id))
            tickets.append(int(self.beneficiary4.id))
            tickets.append(int(self.beneficiary5.id))
            tickets.append(int(self.beneficiary6.id))
            tickets.append(int(self.beneficiary7.id))
            tickets.append(int(self.beneficiary8.id))
            tickets.append(int(self.beneficiary9.id))

        if len(set(tickets)) < int(self.tickets_request):
            raise ValidationError('¡Esta seleccionando beneficiarios repetidos!')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrLeavesInh, self).create(vals_list)
        if res.code in ['PFLY','SCP','SCSE']:
            employee_noti_id = self.env['hr.employee'].sudo().search([('notify_validate_turns','=',True)])
            if employee_noti_id:
                request_type = res.holiday_status_id.name
                mail = self.env['mail.mail'].sudo().create({
                    'subject': "Solicitud %s creada por %s"%(request_type,res.employee_id.name),
                    'body_html': f"""<p>Se ha creado una solicitud de {request_type} para que pueda ser revisada</p>""",
                    'email_to': employee_noti_id.user_id.login,
                })
                mail.send()
        return res

    def send_email(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        template_id = self.env.ref('portal_cm.rrhh_notification_pv_template')
        template_ctx = {'action_url': base_url}
        template_id.attachment_ids = [(6, 0, self.supported_attachment_ids.ids)]
        template_id.with_context(**template_ctx).sudo().send_mail(self.id,force_send=True)

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):
        if self.env.context.get('leave_skip_date_check', False):
            return

        all_employees = self.all_employee_ids
        all_leaves = self.search([
            ('date_from', '<', max(self.mapped('date_to'))),
            ('date_to', '>', min(self.mapped('date_from'))),
            ('employee_id', 'in', all_employees.ids),
            ('id', 'not in', self.ids),
            ('state', 'not in', ['cancel', 'refuse']),
        ])
        for holiday in self:
            domain = [
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
            ]

            employee_ids = (holiday.employee_id | holiday.employee_ids).ids
            search_domain = domain + [('employee_id', 'in', employee_ids)]
            conflicting_holidays = all_leaves.filtered_domain(search_domain)

            if conflicting_holidays:
                conflicting_holidays_list = []
                # Do not display the name of the employee if the conflicting holidays have an employee_id.user_id equivalent to the user id
                holidays_only_have_uid = bool(holiday.employee_id)
                holiday_states = dict(conflicting_holidays.fields_get(allfields=['state'])['state']['selection'])
                for conflicting_holiday in conflicting_holidays:
                    conflicting_holiday_data = {}
                    conflicting_holiday_data['employee_name'] = conflicting_holiday.employee_id.name
                    conflicting_holiday_data['date_from'] = format_date(self.env, min(conflicting_holiday.mapped('date_from')))
                    conflicting_holiday_data['date_to'] = format_date(self.env, min(conflicting_holiday.mapped('date_to')))
                    conflicting_holiday_data['state'] = holiday_states[conflicting_holiday.state]
                    if conflicting_holiday.employee_id.user_id.id != self.env.uid:
                        holidays_only_have_uid = False
                    if conflicting_holiday_data not in conflicting_holidays_list:
                        conflicting_holidays_list.append(conflicting_holiday_data)
                if not conflicting_holidays_list:
                    return
                conflicting_holidays_strings = []
                if holidays_only_have_uid:
                    for conflicting_holiday_data in conflicting_holidays_list:
                        conflicting_holidays_string = _('from %(date_from)s to %(date_to)s - %(state)s',
                                                        date_from=conflicting_holiday_data['date_from'],
                                                        date_to=conflicting_holiday_data['date_to'],
                                                        state=conflicting_holiday_data['state'])
                        conflicting_holidays_strings.append(conflicting_holidays_string)
                    if holiday.code not in ['PFLY','SCP','SCSE']:
                        raise ValidationError(_("""\
    Ya programó tiempo personal que se sobrepone con este periodo:\n
    %s
    Intentar programar dos veces su tiempo personal ¡no mejorará sus vacaciones!\n
    """,
                            "\n".join(conflicting_holidays_strings)))
                for conflicting_holiday_data in conflicting_holidays_list:
                    conflicting_holidays_string = "\n" + _('%(employee_name)s - from %(date_from)s to %(date_to)s - %(state)s',
                                                    employee_name=conflicting_holiday_data['employee_name'],
                                                    date_from=conflicting_holiday_data['date_from'],
                                                    date_to=conflicting_holiday_data['date_to'],
                                                    state=conflicting_holiday_data['state'])
                    conflicting_holidays_strings.append(conflicting_holidays_string)
                if holiday.code not in ['PFLY','SCP','SCSE']:
                    raise ValidationError(_(
                        "Un empleado ya programó un permiso que coincide con este periodo: %s",
                        "".join(conflicting_holidays_strings)))

class hrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    show_absences_menu = fields.Boolean(string="Ausencias")
    show_pfly_menu = fields.Boolean(string="Programa a Volar")
    show_reserve_room_menu = fields.Boolean(string="Reservar sala")
    show_download_signature_menu = fields.Boolean(string="Descargar Firma")

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    show_absences_menu = fields.Boolean(string="Ausencias")
    show_pfly_menu = fields.Boolean(string="Programa a Volar")
    show_reserve_room_menu = fields.Boolean(string="Reservar sala")
    show_download_signature_menu = fields.Boolean(string="Descargar Firma")