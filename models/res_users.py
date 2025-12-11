# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    reserva_ids = fields.One2many(
        'reserva.reserva',
        'usuario_id',
        string='Mis Reservas'
    )
    
    reservas_count = fields.Integer(
        string='Total de Reservas',
        compute='_compute_reservas_count'
    )
    
    def _compute_reservas_count(self):
        for user in self:
            user.reservas_count = len(user.reserva_ids)