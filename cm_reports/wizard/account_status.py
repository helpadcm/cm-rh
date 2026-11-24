# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import ast
import base64


class wizard_account_status(models.TransientModel):
    _name = "cm_reports.wizard_account_status"
    _description = "Estado de cuenta Clientes"

    date_to = fields.Date(string="Fecha Final")
    date_start = fields.Date(string="Fecha de Inicio")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    partner_ids = fields.Many2many('res.partner', string="Clientes")
    payment_state = fields.Selection([('paid', 'Pagado Totalmente'), ('pending', 'Pendientes de pago')], default="pending", string="Estado de pago")
    zero_balance = fields.Boolean(string="Con Saldo Distinto de cero")

    # campos para correo
    send_email = fields.Boolean(string="Enviar por correo electrónico")
    partner_email = fields.Char(string="Correo Electrónico")

    @api.onchange('partner_ids', 'partner_id')
    def _onchange_partner_ids(self):
        for wizard in self:
            if wizard.partner_ids:
                emails = [partner.email for partner in wizard.partner_ids if partner.email]
                wizard.partner_email = ", ".join(emails) if emails else ''
            elif wizard.partner_id:
                wizard.partner_email = wizard.partner_id.email or ''
            else:
                wizard.partner_email = ''

    def report_status(self):
        datas = {
            'date_to': self.date_to,
            'date_start': self.date_start,
            'partner_id': self.partner_id.ids,
            'partner_ids': self.partner_ids.ids,
            'zero_balance': self.zero_balance,
            'payment_state': self.payment_state
        }
        if self.env.context.get('export_excel'):
            return self.env.ref('cm_reports.report_account_status_xls').report_action(self, data=datas)

        return self.env.ref('cm_reports.account_status_report_account_status').report_action(self, data=datas)

    def action_send_email_report(self):
        """Abre la ventana emergente para previsualizar, editar y enviar el correo con el reporte"""
        self.ensure_one()
        if not self.partner_email:
            raise ValidationError("Debe indicar al menos un correo electrónico válido para realizar el envío.")

        # Validar que solo haya un correo electrónico
        raw_emails = [
            e.strip()
            for e in self.partner_email.replace(';', ',').split(',')
            if e.strip()
        ]
        if len(raw_emails) > 1:
            raise ValidationError(
                "Solo se permite un correo electrónico. Por favor elimine los correos adicionales y deje solo uno."
            )

        single_email = raw_emails[0]

        # Buscar la plantilla de correo
        template = self.env.ref('cm_reports.email_template_account_status', raise_if_not_found=False)
        if not template:
            raise ValidationError("No se encontró la plantilla de correo electrónico configurada.")

        # Conversión de fechas a texto seguro para el reporte
        date_start_str = self.date_start.strftime('%Y-%m-%d') if self.date_start else ''
        date_to_str = self.date_to.strftime('%Y-%m-%d') if self.date_to else ''

        datas = {
            'date_to': date_to_str,
            'date_start': date_start_str,
            'partner_id': self.partner_id.ids,
            'partner_ids': self.partner_ids.ids,
            'zero_balance': self.zero_balance,
            'payment_state': self.payment_state,
        }

        # Generar el PDF del reporte
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'cm_reports.account_status_report_account_status',
            self.ids,
            data=datas
        )

        # Crear el adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f'Estado_de_Cuenta_{fields.Date.today()}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'cm_reports.wizard_account_status',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_model': 'cm_reports.wizard_account_status',
                'default_res_ids': self.ids,
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'default_email_to': single_email,
                'default_cm_email_cc': 'marina@cmairlines.com',
                'default_reply_to': False,
                'default_attachment_ids': [(4, attachment.id)],
                'force_email': True,
            }
        }


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    cm_email_cc = fields.Char(string="Cc.")

    def _get_parsed_res_ids(self):
        parsed_ids = []
        for wizard in self:
            raw = wizard.res_ids
            if isinstance(raw, (list, tuple)):
                for item in raw:
                    if isinstance(item, int):
                        parsed_ids.append(item)
                    elif isinstance(item, str):
                        try:
                            val = ast.literal_eval(item)
                            if isinstance(val, list):
                                parsed_ids.extend(int(x) for x in val if isinstance(x, (int, str)) and str(x).isdigit())
                            elif str(val).isdigit():
                                parsed_ids.append(int(val))
                        except Exception:
                            if item.strip().isdigit():
                                parsed_ids.append(int(item.strip()))
            elif isinstance(raw, str) and raw.strip():
                try:
                    val = ast.literal_eval(raw)
                    if isinstance(val, list):
                        parsed_ids.extend(int(x) for x in val if isinstance(x, (int, str)) and str(x).isdigit())
                    elif str(val).isdigit():
                        parsed_ids.append(int(val))
                except Exception:
                    if raw.strip().isdigit():
                        parsed_ids.append(int(raw.strip()))
        return list(set(parsed_ids))

    def _action_send_mail(self, auto_commit=False):
        for wizard in self:
            if wizard.cm_email_cc and 'email_cc' in wizard._fields:
                wizard.email_cc = wizard.cm_email_cc
        res = super()._action_send_mail(auto_commit=auto_commit)
        single_email = (self.env.context.get('default_email_to') or '').strip()
        res_ids = self._get_parsed_res_ids()
        if single_email and res_ids:
            mails = self.env['mail.mail'].sudo().search([
                ('model', '=', 'cm_reports.wizard_account_status'),
                ('res_id', 'in', res_ids),
            ], order='id desc', limit=1)
            if mails:
                mails.write({
                    'email_to': single_email,
                    'recipient_ids': [(5, 0, 0)],
                })
        return res