import base64
from odoo import api, exceptions, models, fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

states = [('created', 'Creada'), ('sent', 'Enviada'), ('received', 'Recibida'),
         ('delivered', 'Entregada'), ('abandoned', 'Abandonada'), ('desechada', 'Desechada'), ('canceled', 'Cancelada')] 

class BillLading(models.Model):
    _name = 'cargo.bill'
    _description = "Guias de Carga"
    _inherit = ['mail.thread','mail.activity.mixin']

    state = fields.Selection(states, string="Estado", default="created", tracking=True)
    content_description = fields.Text(string="Descripcion", tracking=True)
    observations = fields.Text(string="Observaciones", tracking=True)
    name = fields.Char(string="Guia #", default="Guia Borrador")
    partner_id = fields.Many2one('res.partner', string='Cliente')
    modality = fields.Selection([('upon_delivery','Por Cobrar'),('credit','Credito'),('counted','Contado')], string="Modalidad")
    discount_code = fields.Char(string="Codigo Descuento", related="order_id.discount_id.code")
    # Sender
    sender_name = fields.Char(string="Remitente", tracking=True)
    id_sender = fields.Char(string="Identidad Remitente", tracking=True)
    sender_phone = fields.Char(string="Telefono Remitente", tracking=True)
    # lost_reason_id = fields.Many2one("crm.lost.reason", "Motivo DESECHADA")
    # Receiver
    receiver_name = fields.Char(string="Destinatario", tracking=True)
    id_receiver = fields.Char(string="Identidad Destinatario", tracking=True)
    receiver_phone = fields.Char(string="Telefono Destinatario", tracking=True)

    destination_id = fields.Many2one("cargo.station", string="Destino", tracking=True)
    origin_id = fields.Many2one("cargo.station", string="Origen", tracking=True)

    order_id = fields.Many2one('sale.order.handling', string="Orden de Venta")
    payment_state = fields.Selection(string="Estado de Pago", related="order_id.payment_state")
    cart_line_id = fields.Many2one('cart.order.handling',string="Linea de carrito")

    content_description_ids = fields.Many2many('cargo.content.description', string="Descripcion del Contenido")
    type_id = fields.Many2one('cargo.type', string="Tipo de Envio")
    options = fields.Selection(related="type_id.options")
    lost_reason_id = fields.Many2one("handling.lost.reason", "Motivo DESECHADA")

    weight = fields.Float(string="Peso LBS")
    qty = fields.Float(string="Cantidad")
    volumen = fields.Float(string="Volumen")
    product_id = fields.Many2one('product.product',string="Producto")
    amount_total = fields.Float(string="Total")
    amount_total_lps = fields.Float(string="Total (Lps)")

    group_invoice_id = fields.Many2one('cargo.invoice.group_guides',string="Facturacion de guias")

##################################  MANIFEST FIELDS  ##############################################
    cargo_manifest_id = fields.Many2one('cargo.manifest', string="Manifiesto de Carga")
    bill_log_ids = fields.One2many('cargo.bill_logs', 'bill_landing_id', string="Bitacora")

    def print_guides(self):
        data = {
            'order_id': self.order_id.id,
            'print_guides': False
            }
        return self.env.ref('cm_cargo_handling.action_invoice_guide_format').report_action(self, data=data)

    def deliver_cargo(self):
        for line in self:
            if line.modality in ['upon_delivery', 'counted']:
                if line.order_id.discount_id.code not in ['COMAIL','G10']:
                    if line.order_id.move_id.prestate2 != 'paid' and line.order_id.move_id.payment_state not in ['paid','in_payment']:
                        raise UserError(
                                "La modalidad de la guia de carga es por cobrar o de contado y la factura "
                                "no se encuentra pagada, Se debe pagar la factura para entregar la encomienda"
                                )
                line.state = 'delivered'
                line.order_id.state = 'invoiced'
                self.create_log('delivered', 'Entregado')
            else:
                line.state = 'delivered'
                line.order_id.state = 'invoiced'
                self.create_log('delivered', 'Entregado')

    def create_log(self, state, obs):
        log_obj = self.env['cargo.bill_logs']
        manifest_id = self.cargo_manifest_id
        if not manifest_id and self.bill_log_ids:
            last_line_id = self.bill_log_ids[len(self.bill_log_ids) - 1]
            manifest_id = last_line_id.manifest_id

        if manifest_id:
            res = {
                'manifest_id': manifest_id.id,
                'bill_landing_id': self.id,
                'observations': obs,
                'type': state
            }
            log_obj.create(res)


    def undelive_cargo(self):
        for line in self:
            line.state = 'received'

    def show_invoice(self):
        if not self.order_id.move_id:
            raise ValidationError("No hay factura creada para esta guia")

        return {
            'name': _('Factura de encomienda'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.order_id.move_id.id,
            'target': 'current',
            'context': {},
        }

    def show_order(self):
        if not self.order_id:
            raise ValidationError("No hay orden creada para esta guia")

        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.handling',
            'view_mode': 'form',
            'res_id': self.order_id.id,
            'target': 'current',
            'context': {},
        }

    def abandoned_cargo(self):
        for line in self:
            line.state = 'abandoned'

    def action_desechar(self):
        for record in self:
            today = datetime.now()
            midnight_totay = today.replace(hour=0, minute=0, second=0, microsecond=0)
            # if midnight_totay > record.create_date:
            #     raise ValidationError("Las guias deben ser del dia actual")
            
            if record.create_uid.id == self.env.user.id or self.env.user.has_group("cm_cargo_handling.group_desechar_guias"):
                if record.order_id.payment_state == "paid":
                    raise ValidationError("La Factura ya se encuentra Pagada")

                if record.order_id.payment_state == "partial":
                    raise ValidationError("La Factura ya tiene pagos de caja")

                val = {'default_guia_ids': [(6,0,record.ids)]}
                res = {
                    'type': 'ir.actions.act_window',
                    'name': _("Motivo de Desechar"),
                    'res_model': 'cm_cargo_handling.desechar_guia',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': val,
                    'target': 'new',
                    }

                return res
            else:
                raise ValidationError("Debe ser el usuario que creo la guia o tener el permiso para desechar todas la guias")

    def pay_invoice(self):
        if not self.order_id.move_id:
            self.order_id.create_invoices()
            self.order_id.move_id.action_post()
            return self.order_id.register_payment()
        else:
            return self.order_id.register_payment()

    def delivery_order_gua(self):
        guides_ids = self.search([('destination_id.ref','=','GUA-ATO')])
        if guides_ids:
            for guide in guides_ids:
                if guide.product_id.default_code == '890':
                    guide.state = 'delivered'

    @api.model
    def generate_and_send_report(self):
        # Generar el PDF del reporte
        report_ref = 'cm_cargo_handling.action_daily_sales_report'  # Referencia del reporte
        report_action = self.env.ref(report_ref)
        pdf_content, _ = report_action._render_qweb_pdf(
            report_ref=report_ref,
            data={
            'initial_date': datetime.now().date().strftime('%Y-%m-%d'),
            'final_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        pdf_base64 = base64.b64encode(pdf_content)

        # Crear adjunto con el contenido del PDF
        pdf_name = f"Reporte_de Venta Diaria_{datetime.now().date()}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'type': 'binary',
            'datas': pdf_base64,
            'mimetype': 'application/pdf',
            'res_model': 'bill.cargo',
            'res_id': self.id,
        })

        body = """
            <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
                    <tr>
                        <td align="center">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
                                <tbody>
                                    <!-- HEADER -->
                                    <tr>
                                        <td align="center" style="min-width: 590px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                <tr>
                                                    <td valign="middle">
                                                        <span style="font-size: 10px;">Ventas Diarias por punto de venta</span><br/>
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
                                                            A continuacion se adjunta el reporte de ventas diarias por estacion del dia {date}
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
        """.format(date=datetime.now().date())

        # Crear y enviar correo
        mail = self.env['mail.mail'].create({
            'subject': f'Reporte de Ventas Diarias - {datetime.now().date()}',
            'body_html': body,
            'email_to': 'esevilla@cmairlines.com,martincobian@cmairlines.com',
            'email_cc': 'jgunera@cmairlines.com,jcalix@cmairlines.com,dleiva@cmairlines.com,carmen@cmairlines.com,fosorio@cmairlines.com,hguzman@cmairlines.com,vvargas@cmairlines.com,oavilez@cmairlines.com',
            'attachment_ids': [(4, attachment.id)],
        })
        mail.send()

class cargo_bill_logs(models.Model):
    _name='cargo.bill_logs'
    _order="create_date desc"
    _description = "Bitacora guia de carga"

    bill_landing_id = fields.Many2one('cargo.bill',string="Guia de carga")
    manifest_id =fields.Many2one('cargo.manifest', string="Manifiesto de Carga")
    observations = fields.Text(string="Observaciones")
    type = fields.Selection([('added','Agregado'),('removed','Removido'),('sent','Enviado'),('received','Recibido'),('delivered','Entregado'),('cancelled','Cancelado')], string="Estado")
    shipping_airport_id = fields.Many2one(related='manifest_id.shipping_airport',string="CTI de envio")
    reception_airport_id = fields.Many2one(related='manifest_id.reception_airport',string="CTI de recepcion")