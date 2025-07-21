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

##################################  MANIFEST FIELDS  ##############################################
    cargo_manifest_id = fields.Many2one('cargo.manifest', string="Manifiesto de Carga")
    bill_log_ids = fields.One2many('cargo.bill_logs', 'bill_landing_id', string="Bitacora")

    def deliver_cargo(self):
        for line in self:
            if line.modality in ['upon_delivery', 'counted']:
                if line.order_id.payment_state != 'paid':
                    raise UserError(
                            "La modalidad de la guia de carga es por cobrar o de contado y la factura "
                            "no se encuentra pagado, Se debe pagar la factura para entregar la encomienda"
                            )
                line.state = 'delivered'
                line.order_id.state = 'invoiced'
            else:
                line.state = 'delivered'
                line.order_id.state = 'invoiced'

    def undelive_cargo(self):
        for line in self:
            line.state = 'received'

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

                val = {'default_guia_id': record.id}
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
            return self.order_id.move_id.line_ids.action_register_payment()

class cargo_bill_logs(models.Model):
    _name='cargo.bill_logs'
    _order="create_date desc"
    _description = "Bitacora guia de carga"

    bill_landing_id = fields.Many2one('cargo.bill',string="Guia de carga")
    manifest_id =fields.Many2one('cargo.manifest', string="Manifiesto de Carga")
    observations = fields.Text(string="Observaciones")
    type = fields.Selection([('added','Agregado'),('removed','Removido'),('sent','Enviado'),('received','Recibido'),('cancelled','Cancelado')], string="Estado")
    shipping_airport_id = fields.Many2one(related='manifest_id.shipping_airport',string="CTI de envio")
    reception_airport_id = fields.Many2one(related='manifest_id.reception_airport',string="CTI de recepcion")