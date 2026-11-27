# -*- coding: utf-8 -*-
import base64
import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class WizardAccountStatusEmailInherit(models.TransientModel):
    _inherit = "cm_reports.wizard_account_status"

    send_email = fields.Boolean(string="Enviar por correo electrónico")
    partner_email = fields.Char(string="Correo Electrónico")

    @api.onchange("partner_ids", "partner_id")
    def _onchange_partner_email_cm(self):
        for wizard in self:
            if wizard.partner_ids:
                emails = [
                    p.email.strip()
                    for p in wizard.partner_ids
                    if p.email and p.email.strip()
                ]
                wizard.partner_email = ", ".join(emails) if emails else ""
            elif wizard.partner_id:
                wizard.partner_email = (wizard.partner_id.email or "").strip()
            else:
                wizard.partner_email = ""

    def action_send_email_report(self):
        self.ensure_one()
        if not self.partner_email:
            raise ValidationError("Debe indicar al menos un correo electrónico válido.")

        emails_list = [
            e.strip()
            for e in self.partner_email.replace(";", ",").split(",")
            if e.strip()
        ]
        if not emails_list:
            raise ValidationError("Debe indicar al menos un correo electrónico válido.")

        datas = {
            "date_to": self.date_to.strftime("%Y-%m-%d") if self.date_to else "",
            "date_start": self.date_start.strftime("%Y-%m-%d") if self.date_start else "",
            "partner_id": self.partner_id.ids,
            "partner_ids": self.partner_ids.ids,
            "zero_balance": self.zero_balance,
            "payment_state": self.payment_state,
        }

        pdf_content, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "cm_reports.account_status_report_account_status",
            self.ids,
            data=datas,
        )

        attachment = self.env["ir.attachment"].create({
            "name": f"Estado_de_Cuenta_{fields.Date.today()}.pdf",
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "res_model": "cm_reports.account.status.email.wizard",
            "mimetype": "application/pdf",
        })

        client_name = (
            self.partner_id.name
            or (self.partner_ids[:1].name if self.partner_ids else "cliente")
        )
        date_start_fmt = self.date_start.strftime("%d/%m/%Y") if self.date_start else ""
        date_to_fmt = self.date_to.strftime("%d/%m/%Y") if self.date_to else ""

        body_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333333; line-height: 1.5;">
                <p>Buen día, estimado/a <strong>{client_name}</strong>:</p>
                <p>Por medio de la presente, adjuntamos su Estado de Cuenta con corte al <strong>{date_to_fmt}</strong> para su revisión y gestión de pago correspondiente.</p>
                <p>En caso de haber realizado algún pago reciente, le agradeceremos nos envíe el comprobante para actualizar nuestros registros.</p>
                <p>Para cualquier consulta, puede comunicarse directamente al correo <a href="mailto:marina@cmairlines.com">marina@cmairlines.com</a>.<br/>
                Quedamos a su entera disposición.</p>
                <br/>
                <p>Saludos cordiales,</p>
            </div>
        """

        email_wiz = self.env["cm_reports.account.status.email.wizard"].create({
            "email_to": ", ".join(emails_list),
            "email_cc": "marina@cmairlines.com",
            "subject": f"Estado de cuenta - {date_start_fmt} al {date_to_fmt}",
            "body_html": body_html,
            "attachment_ids": [(6, 0, [attachment.id])],
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Enviar Estado de Cuenta",
            "res_model": "cm_reports.account.status.email.wizard",
            "res_id": email_wiz.id,
            "view_mode": "form",
            "target": "new",
        }


class AccountStatusEmailWizard(models.TransientModel):
    _name = "cm_reports.account.status.email.wizard"
    _description = "Enviar Estado de Cuenta por Correo"

    email_to = fields.Char(string="Para", required=True)
    email_cc = fields.Char(string="Cc.", default="marina@cmairlines.com")
    subject = fields.Char(string="Asunto", required=True)
    body_html = fields.Html(string="Mensaje", sanitize=False)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "cm_account_status_email_wiz_att_rel",
        "wizard_id",
        "attachment_id",
        string="Adjuntos",
    )

    @staticmethod
    def _split_emails(raw):
        if not raw:
            return []
        return [e.strip() for e in raw.replace(";", ",").split(",") if e.strip()]

    def _validate(self, emails, label):
        bad = [e for e in emails if not EMAIL_REGEX.match(e)]
        if bad:
            raise ValidationError(f"Correo inválido en '{label}': {', '.join(bad)}")

    def action_send_email(self):
        self.ensure_one()
        to_list = self._split_emails(self.email_to)
        if not to_list:
            raise ValidationError("Debe indicar al menos un correo en 'Para'.")
        self._validate(to_list, "Para")

        cc_list = self._split_emails(self.email_cc)
        if cc_list:
            self._validate(cc_list, "Cc.")

        mail = self.env["mail.mail"].sudo().create({
            "subject": self.subject,
            "body_html": self.body_html or "",
            "email_from": self.env.user.email_formatted or "marina@cmairlines.com",
            "email_to": ", ".join(to_list),
            "email_cc": ", ".join(cc_list),
            "reply_to": "marina@cmairlines.com",
            "attachment_ids": [(6, 0, self.attachment_ids.ids)],
            "auto_delete": False,
        })
        mail.send()
        return {"type": "ir.actions.act_window_close"}