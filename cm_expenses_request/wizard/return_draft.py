from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class returnDraft(models.TransientModel):
    _name = "expense.return.draft"
    _description = "Regresar a reporte de gastos a borrador"

    description = fields.Text(string="Motivo")

    def sent_to_draft(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        sheet_id = self.env[active_model].search([('id','in',active_ids)])

        for_user = sheet_id.request_id.assign_to_id.name
        email_to = sheet_id.request_id.assign_to_id.user_id.login
        message_txt = self.description
        subject = f'Error en liquidacion'
        
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
                                                        <span style="font-size: 10px;color:black"><h2>Error en su Liquidacion de viaticos</h2></span><br/>
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
                                                            Se encontraron errores en su liquidacion que necesitan ser corregidos, por favor corregirlos y enviar nuevamente a liquidar.<br/><br/>
                                                            <strong>MOTIVOS:</strong><br/>
                                                            {message}<br/>
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

        sheet_id.request_id.state = 'assigned'
        sheet_id.expenses_ids.write({'state': 'draft'})
        sheet_id.state = 'draft'