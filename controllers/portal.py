# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError
from datetime import datetime


class ReservaPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'reservas_count' in counters:
            # Verificar acceso antes de contar
            ReservaReserva = request.env['reserva.reserva']
            if ReservaReserva.check_access_rights('read', raise_exception=False):
                values['reservas_count'] = ReservaReserva.search_count([
                    ('usuario_id', '=', request.env.user.id)
                ])
            else:
                values['reservas_count'] = 0
        return values

    @http.route(['/my/reservas', '/my/reservas/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_reservas(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        ReservaReserva = request.env['reserva.reserva']

        domain = [('usuario_id', '=', request.env.user.id)]

        searchbar_sortings = {
            'fecha': {'label': _('Fecha'), 'order': 'fecha_inicio desc'},
            'name': {'label': _('Número'), 'order': 'name'},
            'estado': {'label': _('Estado'), 'order': 'estado'},
        }

        if not sortby:
            sortby = 'fecha'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('fecha_inicio', '>=', date_begin), ('fecha_inicio', '<=', date_end)]

        reservas_count = ReservaReserva.search_count(domain)

        pager = portal_pager(
            url="/my/reservas",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=reservas_count,
            page=page,
            step=self._items_per_page
        )

        reservas = ReservaReserva.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_reservas_history'] = reservas.ids[:100]

        values.update({
            'date': date_begin,
            'reservas': reservas,
            'page_name': 'reserva',
            'pager': pager,
            'default_url': '/my/reservas',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("reserva_canchas.portal_my_reservas", values)

    @http.route(['/my/reservas/<int:reserva_id>'], type='http', auth="user", website=True)
    def portal_my_reserva_detail(self, reserva_id, access_token=None, **kw):
        try:
            reserva_sudo = self._document_check_access('reserva.reserva', reserva_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'reserva': reserva_sudo,
            'page_name': 'reserva',
        }
        return request.render("reserva_canchas.portal_reserva_page", values)

    @http.route(['/my/reservas/<int:reserva_id>/cancel'], type='http', auth="user", website=True)
    def portal_reserva_cancel(self, reserva_id, **kw):
        try:
            reserva_sudo = self._document_check_access('reserva.reserva', reserva_id)
            if reserva_sudo.estado in ['borrador', 'confirmada']:
                reserva_sudo.action_cancelar()
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        return request.redirect('/my/reservas/%s' % reserva_id)

    @http.route(['/my/reservas/nueva'], type='http', auth="user", website=True)
    def portal_nueva_reserva_canchas(self, **kw):
        canchas = request.env['reserva.cancha'].sudo().search([
            ('activa', '=', True),
            ('estado', '=', 'disponible')
        ])
        
        values = {
            'canchas': canchas,
            'page_name': 'nueva_reserva',
        }
        return request.render("reserva_canchas.portal_nueva_reserva_canchas", values)

    @http.route(['/my/reservas/nueva/<int:cancha_id>'], type='http', auth="user", website=True)
    def portal_nueva_reserva_form(self, cancha_id, **kw):
        try:
            cancha = request.env['reserva.cancha'].sudo().browse(cancha_id)
            if not cancha.exists() or not cancha.activa or cancha.estado != 'disponible':
                return request.redirect('/my/reservas/nueva')
        except (AccessError, MissingError):
            return request.redirect('/my/reservas/nueva')

        values = {
            'cancha': cancha,
            'page_name': 'nueva_reserva',
        }
        return request.render("reserva_canchas.portal_nueva_reserva_form", values)

    @http.route(['/my/reservas/crear'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_crear_reserva(self, **post):
        try:
            cancha_id = int(post.get('cancha_id'))
            fecha_inicio_str = post.get('fecha_inicio')
            fecha_fin_str = post.get('fecha_fin')
            notas = post.get('notas', '')

            # Validar que se recibieron los datos necesarios
            if not cancha_id or not fecha_inicio_str or not fecha_fin_str:
                return request.redirect('/my/reservas/nueva?error=Datos incompletos')

            # Convertir strings a datetime
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%dT%H:%M')
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%dT%H:%M')

            # Verificar que la cancha existe y está disponible
            cancha = request.env['reserva.cancha'].sudo().browse(cancha_id)
            if not cancha.exists() or not cancha.activa or cancha.estado != 'disponible':
                return request.redirect('/my/reservas/nueva?error=Cancha no disponible')

            # Crear la reserva
            reserva = request.env['reserva.reserva'].create({
                'cancha_id': cancha_id,
                'usuario_id': request.env.user.id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'notas': notas,
                'estado': 'borrador',
            })

            # Confirmar automáticamente
            reserva.action_confirmar()

            return request.redirect('/my/reservas/%s?message=created' % reserva.id)

        except ValidationError as e:
            error_msg = str(e.name) if hasattr(e, 'name') else str(e)
            return request.redirect('/my/reservas/nueva?error=%s' % error_msg)
        except ValueError as e:
            return request.redirect('/my/reservas/nueva?error=Formato de fecha inválido')
        except Exception as e:
            return request.redirect('/my/reservas/nueva?error=Error al crear la reserva. Intente nuevamente')

    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        if not document_sudo:
            raise MissingError(_("Este documento no existe."))
        
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            if not access_token:
                raise
        
        return document_sudo