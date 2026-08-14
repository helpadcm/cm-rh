# -*- coding: utf-8 -*-
from odoo import api, models,fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError,ValidationError

class Cargo_manifest(models.Model):    
    _name = 'cargo.manifest'
    _description = "Manifiesto de carga"
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def _get_shipping_airport(self):
        return self.env.user.station_id.airport_id.id

    @api.model
    def get_actual_date(self):
        return datetime.now()

    flight = fields.Char(string="Vuelo")
    name = fields.Char(string="Numero", tracking=True)
    total_weight = fields.Float(string="Total Peso (lbs)",compute="_get_total_weight")
    # total_vol_weight = fields.Float(string="Total volumetric weight",compute="_get_total_weight")
    shipping_date = fields.Datetime(string="Fecha de Envio", default=datetime.now(),tracking=True)
    reception_date = fields.Datetime(string="Fecha de Recepcion", tracking=True)
    shipping_airport = fields.Many2one('cargo.airport', default=_get_shipping_airport, string="CTI de Envio", tracking=True)
    reception_airport = fields.Many2one('cargo.airport', string="CTI de Recepcion", tracking=True)
    state = fields.Selection([('draft','Borrador'),('sent','Enviado'),('received','Recibido'),('cancelled','Cancelado')], string="Estado", default="draft", tracking=True)
    bill_landing_barcode = fields.Char(string="Codigo de barras")
    shipping_observations = fields.Text(string="Observaciones de envio", tracking=True)
    reception_observations = fields.Text(string="Observaciones de recepcion", tracking=True)
    cargo_bill_landing_ids = fields.One2many('cargo.manifest_bill_landing','cargo_manifest_id',string="Bill landings")
    cargo_manifest_log_ids = fields.One2many('cargo.manifest_log','cargo_manifest_id',string="Logs")
    abandoned_guides = fields.Boolean(string="Manifiesto de Abandono")
    abandoned_date = fields.Datetime(string="Fecha de abandono", default=get_actual_date, tracking=True)
    abandoned_place = fields.Char(string="Lugar", tracking=True)
    abandoned_members = fields.Char(string="Integrantes", tracking=True)
    abandoned_city = fields.Char(string="Ciudad")

    @api.depends('cargo_bill_landing_ids')
    def _get_total_weight(self):
        sum_weight = 0
        for rec in self:
            if rec.cargo_bill_landing_ids:
                sum_weight = sum(rec.cargo_bill_landing_ids.mapped('weight'))

            rec.total_weight = sum_weight
            

    @api.onchange('bill_landing_barcode')
    def onchange_bill_landing_barcode(self):
        bill_landings_list = []
        actual_ids = []
        for cbl in self.cargo_bill_landing_ids:
            actual_ids.append(cbl.bill_landing_id.id)

        if self.bill_landing_barcode:
            barcode = self.bill_landing_barcode
            barcode = barcode.replace("'","-")
            bill_landings = self.env['cargo.bill'].search([('name','=',barcode),('state','!=','delivered'),('id','not in',actual_ids),('cargo_manifest_id','=',False)])
            for bl in bill_landings:
                if bl.state == 'desechada':
                    raise ValidationError(f"""La guia {bl.name} esta en estado desechada por lo que no se puede manifestar""")
                elif bl.state == 'delivered':
                    raise ValidationError(f"""La guia {bl.name} esta en estado entregada por lo que no se puede manifestar""")
                elif bl.state == 'canceled':
                    raise ValidationError(f"""La guia {bl.name} esta en estado cancelada por lo que no se puede manifestar""")
                elif bl.state == 'abandoned':
                    raise ValidationError(f"""La guia {bl.name} esta en estado abandonada por lo que no se puede manifestar""")
                # for invoice in bl.get_invoice_ids():
                #     if invoice.modality == "counted":
                #         if round(invoice.residual-invoice.amount_prepago,2) > 0.01:
                #             raise(ValidationError("Esta guía de contado tiene saldo, no se podrá manifestar.  Debe ingresar un pago para esta guía"))

                vals = {'cargo_manifest_id': self.id, 'bill_landing_id':bl.id}
                bill_landings_list.append((0, 0, vals))
            self.bill_landing_barcode = False
            self.cargo_bill_landing_ids = bill_landings_list

    def send(self):
        if not self.name:
            sequence = self.shipping_airport.cargo_manifest_sequence_id
            if not sequence:
                raise ValidationError(_('Debe configurar una secuencia para el manifiesto de el aeropuerto de envio'))
            self.name = sequence.next_by_id()
        
        if not self.cargo_bill_landing_ids:
            raise ValidationError("No hay guias de carga para enviar")

        cbl=[]
        for line in self.cargo_bill_landing_ids:

            if not line.bill_landing_id:
                continue
                
            if line.bill_landing_id.state == 'desechada':
                raise ValidationError(f"""La Guia {line.bill_landing_id.name} esta en estado desechada, debe eliminarla del manifiesto antes de enviar""")
            
            line.bill_landing_id.state = 'sent'
            cbl.append(line.bill_landing_id.id)
            res = {
                'manifest_id': self.id,
                'bill_landing_id': line.bill_landing_id.id,
                'observations': self.shipping_observations,
                'type':'sent'
                }
            self.env['cargo.bill_logs'].create(res)
        self.create_log(self.id, cbl, self.shipping_observations,'sent')
        self.state = 'sent'

    def create_log(self, cargo_manifest_id, bill_landing_ids, observations,type):
        values = {
            'cargo_manifest_id': cargo_manifest_id,
            'bill_landing_ids':[(6, 0, bill_landing_ids)],
            'date': datetime.today(),
            'observations': observations,
            'type': type
        }
        self.env['cargo.manifest_log'].create(values)
        
    def print_abandonment_report(self):
        return self.env.ref('cm_cargo_handling.action_abandonment_report_id').report_action(self)

    def finalized_manifest(self):
        peu_id = self.env['cargo.airport'].search([('ref','=','PEU')])
        if peu_id:
            manifest_ids = self.search([('reception_airport','=',peu_id.id),('state','=','sent')])
            if manifest_ids:
                manifest_ids.write({'state': 'received'})

            station_peu_id = self.env['cargo.station'].search([('airport_id','=',peu_id.id)])
            if station_peu_id:
                guide_ids = self.env['cargo.bill'].search([('destination_id','=',station_peu_id.id),('state','in',['sent','received'])])
                if guide_ids:
                    guide_ids.write({'state': 'delivered'})

class Cargo_manifest_bill_landing(models.Model):
    _name   =   'cargo.manifest_bill_landing'
    _description = "Guias de Carga en Manifiesto"

    cargo_manifest_id = fields.Many2one('cargo.manifest',string="Cargo manifest")
    bill_landing_id = fields.Many2one('cargo.bill',string="Guia")
    sender_name = fields.Char(related="bill_landing_id.sender_name")
    weight = fields.Float(related='bill_landing_id.weight')
    destination_id = fields.Many2one(related='bill_landing_id.destination_id')
    observations = fields.Text(related='bill_landing_id.observations',string="Observaciones")
    description = fields.Text(related='bill_landing_id.content_description',string="Descripcion")
    modality = fields.Selection(related='bill_landing_id.modality', string="Modalidad")
    # international_number = fields.Char(related='bill_landing_id.international_number')
    
    def unlink(self):
        for val in self:
            if val.bill_landing_id: 
                if val.bill_landing_id.state in ['sent','received']:
                    val.bill_landing_id.state = 'created'
                
                val.bill_landing_id.cargo_manifest_id = False
                if len(val.bill_landing_id.bill_log_ids) == 1:
                    val.bill_landing_id.bill_log_ids.unlink()
                    
        return super(Cargo_manifest_bill_landing, self).unlink()
        
    @api.model_create_multi
    def create(self,vals):
        res = super(Cargo_manifest_bill_landing, self).create(vals)
        for rec in res:
            if rec.bill_landing_id:
                bl = rec.bill_landing_id
                if not bl.cargo_manifest_id:
                    bl.cargo_manifest_id = rec.cargo_manifest_id.id
                    bl.create_log('added', 'Agregado a Manifiesto')
                else:
                    raise ValidationError(_('La guia de carfa %s ya fue escaneada') %(bl.name))
        return res

class cargo_manifest_logs(models.Model):
    _name = 'cargo.manifest_log'
    _description = "Bitacora del manifiesto de carga"

    cargo_manifest_id = fields.Many2one('cargo.manifest',string="Manifiesto de carga")   
    date = fields.Datetime(string="Fecha")
    observations = fields.Text(string="Observaciones")
    bill_landing_ids = fields.Many2many('cargo.bill',string="Guias de carga")
    type = fields.Selection([('added','Agregado'),('removed','Removido'),('sent','Enviado'),('received','Recibido'),('cancelled','Cancelado')],string="Estado")