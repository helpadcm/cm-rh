import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomInvoiceSend(models.TransientModel):
    _name = 'custom.invoice.send'
    _description = 'Envío Consolidado de Facturas por Cliente'

    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
    email_to = fields.Char(string='Para')
    email_cc = fields.Char(string='Cc', default="marina@cmairlines.com")
    subject = fields.Char(string='Asunto')
    body = fields.Html(string='Cuerpo del Correo', sanitize_style=True)
    
    move_ids = fields.Many2many('account.move', string='Facturas Incluidas')
    attachment_ids = fields.Many2many('ir.attachment', string='Archivos Adjuntos')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        
        if not active_ids:
            return res

        moves = self.env['account.move'].browse(active_ids).filtered(lambda m: m.state == 'posted')
        if not moves:
            raise UserError(_("Debes seleccionar al menos una factura publicada."))

        # Validar que todas las facturas pertenecen al mismo cliente
        partners = moves.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(_(
                "Has seleccionado facturas de distintos clientes (%s).\n"
                "Selecciona únicamente facturas pertenecientes al mismo cliente."
            ) % ", ".join(partners.mapped('name')))

        partner = partners[0]
        res['partner_id'] = partner.id
        res['email_to'] = partner.email
        res['move_ids'] = [(6, 0, moves.ids)]

        # Asunto y Cuerpo por defecto
        if len(moves) == 1:
            res['subject'] = f"Factura {moves.name} - {moves.company_id.name}"
        else:
            res['subject'] = f"Comprobantes y Facturas - {moves.company_id.name}"

        invoice_list_html = ""
        for move in moves:
            if move.is_sync:
                invoice_list_html += f"<li><b>{move.pnrcode}</b> (Fecha: {move.invoice_date.strftime("%d/%m/%Y") or ''})</li>"
            else:
                invoice_list_html += f"<li><b>{move.name}</b> (Fecha: {move.invoice_date.strftime("%d/%m/%Y") or ''})</li>"

        res['body'] = f"""
            <p>Estimado/a <b>{partner.name}</b>,</p>
            <p>Le hacemos llegar adjuntos sus documentos correspondientes:</p>
            <ul>{invoice_list_html}</ul>
            <p>Quedamos a su disposición. Para cualquier consulta o seguimiento, puede comunicarse al correo marina@cmairlines.com.</p>
        """

        # Generar los reportes PDF correspondientes
        all_attachments = self._get_consolidated_attachments(moves)
        res['attachment_ids'] = [(6, 0, all_attachments.ids)]

        return res

    def _get_consolidated_attachments(self, moves):
        """Genera el PDF correspondiente (Boleto o Encomienda) para cada factura."""
        attachments = self.env['ir.attachment']

        for move in moves:
            pdf_content = False

            # 1. VERIFICAR SI ES ENCOMIENDA
            order_id = self.env['sale.order.handling'].search([('move_id', '=', move.id)], limit=1)
            
            if order_id:
                if move.group_invoice_id:
                    data = {
                        'order_id': order_id,
                        'group_invoice_id': move.group_invoice_id.id,
                        'print_guides': False
                    }

                if move.order_handling_id:
                    # Lógica para reporte de Encomienda con estructura de dat
                    data = {
                        'order_id': move.order_handling_id.id,
                        'print_guides': False
                    }
                    
                # Renderizar PDF de Encomienda pasando la estructura de data
                report_action = self.env.ref('cm_cargo_handling.action_invoice_guide_format')
                pdf_content, _ = report_action._render_qweb_pdf(report_action.id, res_ids=[move.id], data=data)

            # 2. SI NO ES ENCOMIENDA, SE GENERA COMO BOLETO
            if move.is_sync:
                report_action = self.env.ref('cm_reports.report_ticket_report_ticket', raise_if_not_found=False)
                if report_action:
                    # SINTAXIS CORREGIDA PARA BOLETO:
                    pdf_content, _ = report_action._render_qweb_pdf(report_action.id, res_ids=[move.id])
                else:
                    # Fallback al reporte nativo de facturas
                    pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('account.account_invoices', res_ids=[move.id])

            # Crear el objeto ir.attachment con el contenido en bytes
            if pdf_content:
                # Codificar el contenido del PDF a Base64
                b64_pdf = base64.b64encode(pdf_content)

                pdf_attachment = self.env['ir.attachment'].create({
                    'name': f"{move.name.replace('/', '_')}.pdf",
                    'type': 'binary',
                    'datas': b64_pdf,  # <--- SE ENVÍA ENCODED EN BASE64
                    'res_model': 'account.move',
                    'res_id': move.id,
                    'mimetype': 'application/pdf',  # <--- ASEGURA EL FORMATO PDF
                })
                attachments |= pdf_attachment

        return attachments

    def action_send_mail(self):
        """Envía un único correo con todas las facturas y sus adjuntos."""
        self.ensure_one()
        
        if not self.email_to:
            raise UserError(_("El cliente %s no tiene correo electrónico configurado.") % self.partner_id.name)

        # Crear y enviar el correo único
        mail_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': self.email_to,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
        }

        if self.email_cc:
            mail_values.update({'email_cc': self.email_cc})

        self.partner_id.email = self.email_to
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        return {'type': 'ir.actions.act_window_close'}