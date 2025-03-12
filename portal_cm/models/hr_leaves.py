from odoo import fields, models, api
from odoo.http import request

class HrLeavesType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string="Codigo")

class HrLeavesInh(models.Model):
    _inherit = 'hr.leave'
    
    tickets_request = fields.Integer(string="Boletos Solicitados", tracking=True)
    code = fields.Char(related="holiday_status_id.code",string="Codigo")
    exit_route_id = fields.Many2one('flight.routes',string="Ruta de Salida", tracking=True)
    return_route_id = fields.Many2one('flight.routes',string="Ruta de Regreso", tracking=True)
    exit_only = fields.Boolean(string="Solo Salida",tracking=True)
    beneficiary1 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 1", tracking=True)
    beneficiary2 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 2", tracking=True)
    beneficiary3 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 3", tracking=True)
    beneficiary4 = fields.Many2one('beneficiaries.detail.list',string="Beneficiario 4", tracking=True)

    def action_approve(self, check_state=True):
        res = super(HrLeavesInh, self).action_approve(check_state)
        if self.holiday_status_id.code == 'VAC':
            if len(self.employee_id.vacation_details_ids) > 0:
                self.employee_id.vacation_details_ids[0].pending_days -= self.number_of_days
            else:
                self.employee_id.early_vacations += self.number_of_days
        elif self.holiday_status_id.code == 'HCOMP':
            if self.request_unit_half:
                hours_taken = 4
            else:
                hours_taken = self.number_of_days * 8
            self.employee_id.compensatory_hours -= hours_taken
        elif self.holiday_status_id.code == 'PFLY':
            if self.exit_only:
                self.employee_id.program_to_fly -= (self.tickets_request/2)
            else:
                self.employee_id.program_to_fly -= self.tickets_request
            self.send_email()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrLeavesInh, self).create(vals_list)
        if res.code == 'PFLY':
            employee_noti_id = self.env['hr.employee'].search([('notify_validate_turns','=',True)])
            if employee_noti_id:
                mail = self.env['mail.mail'].create({
                    'subject': "Solicitud Programa a volar creada por %s"%(res.employee_id.name),
                    'body_html': "<p>Se ha creado una solicitud del programa a volar para que pueda ser revisada</p>",
                    'email_to': employee_noti_id.user_id.login,
                })
                mail.send()
        return res

    def send_email(self):
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        template_id = self.env.ref('portal_cm.rrhh_notification_pv_template')
        template_ctx = {'action_url': base_url}
        template_id.attachment_ids = [(6, 0, self.supported_attachment_ids.ids)]
        template_id.with_context(**template_ctx).send_mail(self.id,force_send=True)

class hrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    show_absences_menu = fields.Boolean(string="Mostrar menu de ausencias en portal")
    show_pfly_menu = fields.Boolean(string="Mostrar menu de PV en portal")

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    show_absences_menu = fields.Boolean(string="Mostrar menu de ausencias en portal")
    show_pfly_menu = fields.Boolean(string="Mostrar menu de PV en portal")