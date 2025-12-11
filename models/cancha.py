# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Cancha(models.Model):
    _name = 'reserva.cancha'
    _description = 'Cancha Deportiva'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'nombre'

    nombre = fields.Char(
        string='Nombre',
        required=True,
        tracking=True
    )
    
    tipo = fields.Selection([
        ('futbol', 'Fútbol'),
        ('basquet', 'Básquetbol'),
        ('voley', 'Vóleibol'),
        ('tenis', 'Tenis'),
        ('padel', 'Pádel'),
        ('otro', 'Otro')
    ], string='Tipo de Cancha', required=True, default='futbol', tracking=True)
    
    descripcion = fields.Text(string='Descripción')
    
    capacidad = fields.Integer(
        string='Capacidad (personas)',
        default=10
    )
    
    precio_hora = fields.Float(
        string='Precio por Hora',
        required=True,
        default=50.0,
        tracking=True
    )
    
    estado = fields.Selection([
        ('disponible', 'Disponible'),
        ('mantenimiento', 'En Mantenimiento'),
        ('inactiva', 'Inactiva')
    ], string='Estado', default='disponible', required=True, tracking=True)
    
    imagen = fields.Image(
        string='Imagen',
        max_width=1024,
        max_height=1024
    )
    
    activa = fields.Boolean(
        string='Activa',
        default=True,
        tracking=True
    )
    
    reserva_ids = fields.One2many(
        'reserva.reserva',
        'cancha_id',
        string='Reservas'
    )
    
    reservas_count = fields.Integer(
        string='Total Reservas',
        compute='_compute_reservas_count'
    )
    
    ubicacion = fields.Char(string='Ubicación')
    
    notas = fields.Text(string='Notas')
    
    @api.depends('reserva_ids')
    def _compute_reservas_count(self):
        for record in self:
            record.reservas_count = len(record.reserva_ids)
    
    @api.constrains('precio_hora')
    def _check_precio_hora(self):
        for record in self:
            if record.precio_hora < 0:
                raise ValidationError(_('El precio por hora no puede ser negativo.'))
    
    @api.constrains('capacidad')
    def _check_capacidad(self):
        for record in self:
            if record.capacidad < 1:
                raise ValidationError(_('La capacidad debe ser al menos 1 persona.'))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.nombre} ({dict(record._fields['tipo'].selection).get(record.tipo)})"
            result.append((record.id, name))
        return result
    
    def action_set_mantenimiento(self):
        self.write({'estado': 'mantenimiento'})
    
    def action_set_disponible(self):
        self.write({'estado': 'disponible'})
    
    def action_set_inactiva(self):
        self.write({'estado': 'inactiva'})