# -*- coding: utf-8 -*-
{
    'name': 'Reserva de Canchas Deportivas',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Gestión de reservas de canchas deportivas',
    'description': """
        Módulo para gestionar reservas de canchas deportivas
        ======================================================
        * Gestión de canchas deportivas
        * Sistema de reservas con validación de disponibilidad
        * Portal web para usuarios
        * Roles: Admin, Staff y Usuario
    """,
    'author': 'Tu Nombre',
    'website': 'https://www.tuempresa.com',
    'depends': ['base', 'web', 'portal', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/cancha_views.xml',
        'views/reserva_views.xml',
        'views/portal_templates.xml',
        'data/cancha_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}