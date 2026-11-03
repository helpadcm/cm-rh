from odoo import models, api
from odoo.tools import html_escape


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields_list):
        res = super(MailComposeMessage, self).default_get(fields_list)

        # Solo si la ventana se abre desde un Pago (account.payment)
        if self.env.context.get('active_model') == 'account.payment':
            payment_id = self.env.context.get('active_id')
            if payment_id:
                payment = self.env['account.payment'].browse(payment_id).exists()

                # Solo pagos de proveedor; los demás conservan el mensaje por defecto de Odoo
                if (payment
                        and payment.payment_type == 'outbound'
                        and payment.partner_type == 'supplier'):
                    partner = html_escape(payment.partner_id.name or '')
                    company = html_escape(payment.company_id.name or '')
                    number = html_escape(payment.name or '')
                    user = html_escape(self.env.user.name or '')

                    res['body'] = f"""
                        <p>Estimado/a {partner},</p>
                        <p>Por medio del presente, el departamento de Cuentas por Pagar de {company} le informa que se ha procesado con éxito el pago correspondiente a sus servicios.</p>
                        <p>Aquí está su recibo de pago <strong>{number}</strong> por un importe de <strong>{payment.currency_id.symbol or 'L'} {payment.amount:,.2f}</strong> de parte de {company}.</p>
                        <br/>
                        <p>Atentamente,</p>
                        <p>{user}</p>
                    """
        return res