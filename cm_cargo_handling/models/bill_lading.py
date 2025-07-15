from odoo import api, exceptions, models, fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

states = [('draft', 'Borrador'), ('created', 'Creada'), ('sent', 'Enviada'), ('received', 'Recibida'),
         ('delivered', 'Entregada'), ('abandoned', 'Abandonada'), ('desechada', 'Desechada'), ('canceled', 'Canceleda')] 

class BillLading(models.Model):
    _name = 'cargo.bill'
    _description = "Guias de Carga"
    _inherit = ['mail.thread','mail.activity.mixin']

    state = fields.Selection(states, string="Estado", default="draft", tracking=True)
    content_description = fields.Text(string="Descripcion", tracking=True)
    observations = fields.Text(string="Observaciones", tracking=True)
    name = fields.Char(string="Guia #", default="Guia Borrador")
    partner_id = fields.Many2one('res.partner', string='Cliente')
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
    cart_line_id = fields.Many2one('cart.order.handling',string="Linea de carrito")

    content_description_ids = fields.Many2many('cargo.content.description', string="Descripcion del Contenido")
    type_id = fields.Many2one('cargo.type', string="Tipo de Envio")
    options = fields.Selection(related="type_id.options")

    weight = fields.Float(string="Peso LBS")