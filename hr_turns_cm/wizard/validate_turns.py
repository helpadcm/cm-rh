# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime

class validateTurn(models.TransientModel):
    _name = 'hr.validate.turns'
    _description = "Validador de turnos"

    @api.model
    def _get_user_default(self):
        return self.env.user.id

    turn = fields.Selection(string="Turno", selection=lambda self: self.get_options())
    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)

    def get_options(self):
        user = self.env.user.id
        turns = self.env['hr.turn.registration'].search(['|',('leader_id.user_id','=',user),('responsible_id.user_id','=',user),('state','=','draft')])
        options_name = set(turns.mapped('name'))
        return [(opt, opt) for opt in options_name]

    def validate_turns(self):
        name_turn = self.turn
        turn_ids = self.env['hr.turn.registration'].search(['|',('leader_id.user_id','=',self.user_id.id),('responsible_id.user_id','=',self.user_id.id),('name','=',name_turn)])
        turn_ids.write({'state': 'validated'})
        responsible_rrhh_id = self.env['hr.employee'].search([('notify_validate_turns','=',True)])
        if responsible_rrhh_id:
            body_mail = f"""
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
                                                        <span style="font-size: 10px;">Validacion de Turnos</span><br/>
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
                                                            Hola {responsible_rrhh_id.name},<br/><br/>
                                                            El colaborador {self.user_id.name} ha validado los turnos para la {name_turn}.
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
            """

            mail = self.env['mail.mail'].sudo().create({
                'subject': 'Turnos de la %s '%(name_turn),
                'body_html': body_mail,
                'email_to': responsible_rrhh_id.work_email
            })
            mail.send()
        return True