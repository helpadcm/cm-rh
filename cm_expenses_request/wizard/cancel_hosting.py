from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class cancelHosting(models.TransientModel):
    _name = "expense.cancel.hosting"
    _description = "Cancelar hospedaje"

    @api.model
    def default_get(self, fields):
        rec = super(cancelHosting, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        req_id = self.env[active_model].search([('id','=',active_id)])
        if req_id.lodging_details_ids:
            lodging_details = []
            for detail in req_id.lodging_details_ids:
                lodging_details.append((0, 0, {
                    'cti_id': detail.cti_id.id,
                    'check_in_date': detail.check_in_date,
                    'check_out_date': detail.check_out_date,
                    'lodging_id': detail.lodging_id.id,
                    'req_id': detail.id,
                }))
            rec['lodging_details_ids'] = lodging_details
        rec['req_id'] = req_id.id
        return rec

    lodging_details_ids = fields.One2many('expenses.cancel.lodging','request_id',string="Detalles de hospedaje")
    req_id = fields.Many2one('cm.expenses.request',string="Solicitud de viáticos")

    def cancel_hosting(self):
        ctis_name = ''
        if not self.lodging_details_ids:
            raise ValidationError("Debe agregar al menos un detalle de hospedaje para enviar la solicitud.")

        # Generación de filas de la tabla
        table_rows = []
        for lodging in self.lodging_details_ids:
            if lodging.cancel_reason:
                table_rows.append(f"""
                <tr>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; color: #334155; text-align: center;">
                        {lodging.cti_id.ref or ''}
                    </td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; color: #334155; text-align: left;">
                        {lodging.lodging_id.name or ''}
                    </td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; color: #334155; text-align: center;">
                        {lodging.check_in_date.strftime("%d/%m/%Y") or ''}
                    </td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; color: #334155; text-align: center;">
                        {lodging.check_out_date.strftime("%d/%m/%Y") or ''}
                    </td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; color: #334155; text-align: left;">
                        {lodging.cancel_reason or '-'}
                    </td>
                </tr>
                """)
                lodging.req_id.status = 'canceled'

        if table_rows:
            rows_html = "".join(table_rows)

            table_body = f"""
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-top: 15px; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #2C3E50; color: #ffffff;">
                        <th style="padding: 10px 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: center;">Estación</th>
                        <th style="padding: 10px 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: left;">Hospedaje</th>
                        <th style="padding: 10px 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: center;">Entrada</th>
                        <th style="padding: 10px 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: center;">Salida</th>
                        <th style="padding: 10px 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: left;">Motivo de Cancelación</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """

            body = f"""
            <div style="background-color: #F8FAFC; width: 100%; margin: 0; padding: 30px 0; font-family: Arial, sans-serif;">
                <!--[if mso]>
                <table align="center" border="0" cellspacing="0" cellpadding="0" width="600">
                <tr>
                <td align="center" valign="top" width="600">
                <![endif]-->
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; border-collapse: separate;">
                    <tbody>
                        <!-- HEADER -->
                        <tr>
                            <td style="padding: 24px 25px 15px 25px; background-color: #ffffff; border-bottom: 2px solid #F1F5F9;">
                                <h2 style="font-size: 20px; font-weight: bold; color: #1E293B; margin: 0;">
                                    Información de Hospedaje
                                </h2>
                            </td>
                        </tr>
                        <!-- CONTENT -->
                        <tr>
                            <td style="padding: 20px 25px; font-size: 14px; line-height: 1.6; color: #334155;">
                                <p style="margin: 0 0 15px 0;">
                                    Estimado(a),
                                </p>
                                <p style="margin: 0 0 15px 0;">
                                    Se ha solicitado la cancelación de hospedaje asociado a la solicitud de viáticos <strong>{self.req_id.name}</strong> por parte de <strong>{self.req_id.assign_to_id.name}</strong>.
                                </p>
                                <p style="margin: 0 0 10px 0; font-weight: bold; color: #1E293B;">
                                    Detalles de la cancelación:
                                </p>
                                
                                {table_body}
                                
                                <p style="margin: 20px 0 0 0;">
                                    Saludos cordiales,<br/>
                                </p>
                            </td>
                        </tr>
                        <!-- FOOTER -->
                        <tr>
                            <td style="padding: 15px 25px; background-color: #F8FAFC; border-top: 1px solid #E2E8F0; text-align: center; font-size: 12px; color: #94A3B8;">
                                Este es un mensaje automático, por favor no responda directamente a este correo.
                            </td>
                        </tr>
                    </tbody>
                </table>
                <!--[if mso]>
                </td>
                </tr>
                </table>
                <![endif]-->
            </div>
            """

            mail = self.env['mail.mail'].sudo().create({
                'subject': f"Solicitud de cancelacion hospedaje",
                'body_html': body,
                'email_from': self.req_id.assign_to_id.user_id.login,
                'email_to': 'esevilla@cmairlines.com',
                'email_cc': 'rosa@cmairlines.com',
            })
            mail.send()

class lodgingCancel(models.TransientModel):
    _name = 'expenses.cancel.lodging'
    _description = "Cancelar detalles de Hospedaje"

    request_id = fields.Many2one('expense.cancel.hosting',string="Solicitud")
    req_id = fields.Many2one('cm.expenses.request.lodging',string="Detalle de gasto de hospedaje")
    cti_id = fields.Many2one('cargo.airport',string="Estacion")
    check_in_date = fields.Date(string="Fecha de ingreso")
    check_out_date = fields.Date(string="Fecha de salida")
    lodging_id = fields.Many2one('expense.lodging.cobus',string="Lugar de hospedaje")
    status = fields.Selection([('active','Activo'),('canceled','Cancelado')],string="Estado",default='active')
    cancel_reason = fields.Text(string="Motivo de cancelacion")