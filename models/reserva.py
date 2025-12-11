# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class Reserva(models.Model):
    _name = 'reserva.reserva'
    _description = 'Reserva de Cancha'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'fecha_inicio desc'

    name = fields.Char(
        string='Número de Reserva',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo')
    )
    
    cancha_id = fields.Many2one(
        'reserva.cancha',
        string='Cancha',
        required=True,
        tracking=True,
        domain=[('activa', '=', True), ('estado', '=', 'disponible')]
    )
    
    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='usuario_id.partner_id',
        store=True
    )
    
    fecha_inicio = fields.Datetime(
        string='Fecha y Hora de Inicio',
        required=True,
        tracking=True
    )
    
    fecha_fin = fields.Datetime(
        string='Fecha y Hora de Fin',
        required=True,
        tracking=True
    )
    
    duracion = fields.Float(
        string='Duración (horas)',
        compute='_compute_duracion',
        store=True
    )
    
    precio_total = fields.Float(
        string='Precio Total',
        compute='_compute_precio_total',
        store=True
    )
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', required=True, tracking=True)
    
    notas = fields.Text(string='Notas')
    
    fecha_creacion = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now,
        readonly=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('reserva.reserva') or _('Nuevo')
        return super(Reserva, self).create(vals)
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_duracion(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                delta = record.fecha_fin - record.fecha_inicio
                record.duracion = delta.total_seconds() / 3600.0
            else:
                record.duracion = 0.0
    
    @api.depends('duracion', 'cancha_id.precio_hora')
    def _compute_precio_total(self):
        for record in self:
            record.precio_total = record.duracion * record.cancha_id.precio_hora
    
    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for record in self:
            if record.fecha_fin <= record.fecha_inicio:
                raise ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio.'))
            
            # Verificar que la reserva sea en el futuro (solo para nuevas reservas)
            if record.estado == 'borrador' and record.fecha_inicio < fields.Datetime.now():
                raise ValidationError(_('No puede crear reservas en el pasado.'))
            
            # Verificar duración mínima (30 minutos) y máxima (8 horas)
            duracion_minutos = (record.fecha_fin - record.fecha_inicio).total_seconds() / 60
            if duracion_minutos < 30:
                raise ValidationError(_('La duración mínima de una reserva es 30 minutos.'))
            if duracion_minutos > 480:
                raise ValidationError(_('La duración máxima de una reserva es 8 horas.'))
    
    @api.constrains('cancha_id', 'fecha_inicio', 'fecha_fin')
    def _check_disponibilidad(self):
        for record in self:
            if record.estado == 'cancelada':
                continue
            
            # Buscar reservas que se superpongan
            reservas_superpuestas = self.env['reserva.reserva'].search([
                ('id', '!=', record.id),
                ('cancha_id', '=', record.cancha_id.id),
                ('estado', 'in', ['confirmada', 'en_curso']),
                '|',
                '&',
                ('fecha_inicio', '<=', record.fecha_inicio),
                ('fecha_fin', '>', record.fecha_inicio),
                '&',
                ('fecha_inicio', '<', record.fecha_fin),
                ('fecha_fin', '>=', record.fecha_fin),
            ])
            
            if reservas_superpuestas:
                raise ValidationError(_(
                    'La cancha no está disponible en el horario seleccionado. '
                    'Ya existe una reserva confirmada en ese período.'
                ))
    
    def action_confirmar(self):
        self.write({'estado': 'confirmada'})
        self._enviar_notificacion_confirmacion()
    
    def action_iniciar(self):
        self.write({'estado': 'en_curso'})
    
    def action_completar(self):
        self.write({'estado': 'completada'})
    
    def action_cancelar(self):
        self.write({'estado': 'cancelada'})
        self._enviar_notificacion_cancelacion()
    
    def action_volver_borrador(self):
        self.write({'estado': 'borrador'})
    
    def _enviar_notificacion_confirmacion(self):
        for record in self:
            record.message_post(
                body=_('La reserva ha sido confirmada para %s desde %s hasta %s.') % (
                    record.cancha_id.nombre,
                    record.fecha_inicio.strftime('%d/%m/%Y %H:%M'),
                    record.fecha_fin.strftime('%d/%m/%Y %H:%M')
                ),
                subject=_('Reserva Confirmada'),
                message_type='notification',
                partner_ids=[record.usuario_id.partner_id.id]
            )
    
    def _enviar_notificacion_cancelacion(self):
        for record in self:
            record.message_post(
                body=_('La reserva para %s ha sido cancelada.') % record.cancha_id.nombre,
                subject=_('Reserva Cancelada'),
                message_type='notification',
                partner_ids=[record.usuario_id.partner_id.id]
            )
    
    def _compute_access_url(self):
        super(Reserva, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/reservas/%s' % record.id
    
    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Reserva_%s' % self.name