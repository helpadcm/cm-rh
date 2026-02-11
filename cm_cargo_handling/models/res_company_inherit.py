# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    conditions = fields.Text('Condiciones de envio')
    acuerdo = fields.Text('Acuerdo de recibido')
    phone_attention = fields.Char('Atencion telefonica')
    whatsapp        =   fields.Char(string="Whatsapp")
    entrust_website =   fields.Char(string="Sitio web encomiendas")
    tgu_int_phone   =   fields.Char(string="Telefono TGU")
    sps_int_phone   =   fields.Char(string="Telefono SPS")

class ResUsersInherit(models.Model):
	_inherit = 'res.users'

	station_id  = fields.Many2one('cargo.station',string="Estacion")

class paymentInherit(models.Model):
    _inherit = 'account.payment'

    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, tracking=True)
    from_cargo = fields.Boolean(string="Desde venta de carga")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super(paymentInherit, self)._prepare_move_line_default_vals(write_off_line_vals=None, force_balance=None)
        if self.journal_id.code == 'EFU' and self.from_cargo:
            for line in res:
                if line.get('debit') > 0:
                    analytic_account_id = self.env['account.analytic.account'].search([('partner_id','=',self.user_id.partner_id.id)])
                    if analytic_account_id:
                        distribution_line = {str(analytic_account_id.id): 100.0}
                        line.update({'analytic_distribution': distribution_line})
                    break
        return res

class partnerInherit(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'client_account', 'phone']

    cargo_client = fields.Boolean(string="Cliente de encomiendas",tracking=True)
    fare_classes_ids = fields.Many2many('fare.clases',string="Clases Tarifarias",tracking=True)
    client_account = fields.Char(string="Cuenta de Cliente",tracking=True)
    modality = fields.Selection([('upon_delivery','Por Cobrar'),('credit','Credito'),('counted','Contado')], string="Modalidad", default="counted",tracking=True)
    discount_id = fields.Many2one('cargo.discount',string="Descuento")
    no_credit = fields.Boolean(string="Sin valor de credito")
    no_volumen = fields.Boolean(string="Sin cargos de volumen")
    default_product_id = fields.Many2one('product.product',string="Producto por defecto")
    credit_limit = fields.Float(string="Limite de Credito($)",tracking=True)
    available_credit = fields.Float(string="Credito Disponible")
    credit_ticket = fields.Boolean(string="Aplica a credito en boletos")
    grouping_invoice = fields.Boolean(string="Agrupar facturas") 

    def write(self,vals):
        if vals.get('cargo_client'):
            if not self.client_account:
                sequence_id = self.env.ref('cm_cargo_handling.sequence_client_account')
                if sequence_id:
                    vals.update({'client_account': sequence_id.next_by_id()})
        res = super(partnerInherit, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(partnerInherit, self).create(vals_list)
        for partner in res:
            if partner.cargo_client and not partner.client_account:
                sequence_id = self.env.ref('cm_cargo_handling.sequence_client_account')
                if sequence_id:
                    partner.client_account = sequence_id.next_by_id()
        return res

    def _get_complete_name(self):
        res = super(partnerInherit, self)._get_complete_name()
        if self.parent_id:
            res = self.name or ''
        return res

class contactListInherit(models.Model):
    _name = 'res.partner.contact'
    _description = "Lista de contactos para encomiendas"
    _rec_names_search = ['name', 'phone', 'identity', 'code']

    name = fields.Char(string="Nombre")
    phone = fields.Char(string="Telefono")
    identity = fields.Char(string="Identidad")
    code = fields.Char(string="Perfil")
    list_number = fields.Integer(string="Numero de contacto en lista")

    @api.onchange('phone')
    def generate_code(self):
        if self.phone:
            contact_existing_ids = self.search([('phone','=',self.phone)])
            if not contact_existing_ids:
                self.list_number = 1
                self.code = f"{self.phone}-01"
            else:
                last_number = max(contact_existing_ids.mapped('list_number'))
                if last_number < 10:
                    self.code = f"{self.phone}-0{last_number + 1}"
                else:
                    self.code = f"{self.phone}-{last_number + 1}"
                self.list_number = (last_number + 1)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(contactListInherit, self).create(vals_list)
        for record in res:
            record.generate_code()
        return res

    @api.model
    def _clean_incomplete_records(self):
        domain = ['|', '|',('name', '=', False),('phone', '=', False),('identity', '=', False)]
        records_ids = self.search(domain)
        
        if records_ids:
            records_ids.unlink()

        return True
