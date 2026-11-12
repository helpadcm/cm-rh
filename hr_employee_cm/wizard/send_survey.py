# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SendSurveyWizard(models.TransientModel):
    _name = "send.survey"
    _description = "Enviar Encuesta de Salida"

    @api.model
    def default_body(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        # Obtenemos el ID del empleado desde el contexto
        employee_id = self.env.context.get("default_employee_id") or self.env.context.get("active_id", "")
        
        if employee_id:
            link_url = f"{base_url}/employee/exit/interview?employee_id={employee_id}"
        else:
            link_url = f"{base_url}/employee/exit/interview"

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
                                                            <span style="font-size: 10px;color:black"><h2>Entrevista de Salida y Evaluación</h2></span><br/>
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
                                                                Agradecemos sinceramente el tiempo, la dedicación y el compromiso brindados durante su trayectoria en CM Airlines. Como parte de nuestros procesos de mejora continua y cierre de ciclo laboral, le solicitamos amablemente su apoyo completando la siguiente entrevista de salida:
                                                                <div style="margin: 16px 0px 16px 0px;">
                                                                    <a href="{url}"
                                                                        style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;">Ir a Formulario</a>
                                                                </div>
                                                                <p>Su opinión es de suma importancia para nosotros. Toda la información proporcionada será tratada con absoluta confidencialidad y nos ayudará a valorar su experiencia laboral y optimizar nuestros procesos internos.</p>

                                                                <p>Agradecemos mucho su tiempo y colaboración, y quedamos atentos a la recepción del formulario. Si tiene alguna duda o inconveniente para ingresar al enlace, estaremos encantados de asistirle.</p>
                                                                <br/>Saludos,<br/><b>Departamento de Recursos Humanos</b><br/><b>CM Airlines</b>
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
            """.format(url=link_url)
        return body

    @api.model
    def default_get(self, fields_list):
        res = super(SendSurveyWizard, self).default_get(fields_list)
        employee_id = self.env.context.get("default_employee_id") or self.env.context.get("active_id")
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            if employee.private_email:
                res['emails'] = employee.private_email
            else:
                res['emails'] = ''
            res['employee_id'] = employee.id
        return res

    emails = fields.Char(string="Correos")
    body_email = fields.Html(string="Contenido del correo", default=default_body)
    employee_id = fields.Many2one('hr.employee', string="Empleado")

    def send_email_form(self):
        self.ensure_one()
        if not self.emails:
            raise UserError(_("Debe especificar al menos un correo electrónico."))
            
        emails_to = [e.strip() for e in self.emails.split(",")]
        for e in emails_to:
            mail_values = {
                'body_html': self.body_email,
                'email_to': e,
                'subject': 'Entrevista de Salida y Evaluación - CM Airlines',
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
        return {'type': 'ir.actions.act_window_close'}