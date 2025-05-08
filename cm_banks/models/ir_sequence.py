# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime
import locale
import pytz

def _select_nextval(cr, seq_name):
    cr.execute("SELECT nextval('%s')" % seq_name)
    return cr.fetchone()

def _update_nogap(self, number_increment):
	number_next = self.number_next

	if not self.env.context.get('no_update',False):
		self._cr.execute("SELECT number_next FROM %s WHERE id=%s FOR UPDATE NOWAIT" % (self._table, self.id))
		self._cr.execute("UPDATE %s SET number_next=number_next+%s WHERE id=%s " % (self._table, number_increment, self.id))
	self.invalidate_cache(['number_next'], [self.id])
	return number_next


class IrSequenceDateRange_inherit(models.Model):
	_inherit = 'ir.sequence.date_range'

	# def _next(self):
	# 	if self.sequence_id.implementation == 'standard':
	# 	    number_next = _select_nextval(self._cr, 'ir_sequence_%03d_%03d' % (self.sequence_id.id, self.id))
	# 	else:
	# 	    number_next = _update_nogap(self, self.sequence_id.number_increment)
	# 	return self.sequence_id.get_next_char(number_next)

class irsecuence(models.Model):
	_name='ir.sequence'
	_inherit = ['ir.sequence','mail.thread']

	code2 = fields.Many2one('ir.sequence.type',string="Codigo Bancario")
	implementation = fields.Selection([('standard', 'Standard'), ('no_gap', 'No gap')],
                                      string='Implementation', required=True, default='no_gap',
                                      help="Two sequence object implementations are offered: Standard "
                                           "and 'No gap'. The later is slower than the former but forbids any"
                                           "gap in the sequence (while they are possible in the former).")

	# def _next_do(self):
	# 	if self.implementation == 'standard':
	# 	    number_next = _select_nextval(self._cr, 'ir_sequence_%03d' % self.id)
	# 	else:
	# 	    number_next = _update_nogap(self, self.number_increment)
	# 	return self.get_next_char(number_next)


class ir_sequence_type(models.Model):
	_name = 'ir.sequence.type'
	_rec_name = 'code'
	_description = "Tipo de secuencia"

	name = fields.Char(string="Nombre")
	code = fields.Char(string="Codigo")



