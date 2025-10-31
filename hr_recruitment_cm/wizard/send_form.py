# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import time

class sendForm(models.TransientModel):
    _name = "applicant.send_form"
    _description = "Enviar Formulario"

    @api.model
    def default_body(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        default_requirement_id = self.env.context.get("default_requirement_id")
        link_url = f"{base_url}/job/apply/{default_requirement_id}"
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
                                                            <span style="font-size: 10px;color:black"><h2>Cuestionario de reclutamiento y seleccion</h2></span><br/>
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
                                                                Agradecemos sinceramente su interés en formar parte de CM Airlines. Como parte del proceso de selección, le solicitamos su apoyo completando el siguiente formulario:
                                                                <div style="margin: 16px 0px 16px 0px;">
                                                                    <a href="{url}"
                                                                        style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 13px;">Ir a Formulario</a>
                                                                </div>
                                                                <p>Esto nos permitirá recibir su información y los documentos necesarios para avanzar de manera ágil en el proceso.</p>

                                                                <p>Agradecemos mucho su tiempo y colaboración, y quedamos atentos a la recepción del formulario. Si tiene alguna duda o inconveniente para ingresar al enlace, estaremos encantados de asistirle.</p>
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
            """.format(url=link_url)
        return body

    emails = fields.Char(string="Correos")
    body_email = fields.Html(string="Contenido", default=default_body)
    requirement_id = fields.Many2one('hr.staff.requirement',string="Requerimiento")

    def send_email_form(self):
        emails_to = self.emails.split(",")
        for e in emails_to:
            mail_values = {
                'body_html': self.body_email,
                'email_to': e,
                'subject': f'Cuestionario de reclutamiento y seleccion',
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()