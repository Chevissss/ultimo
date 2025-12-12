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
        # 1. Primero la seguridad básica (grupos y secuencia)
        'security/security.xml',
        # 2. Vistas (esto crea los modelos y las acciones)
        'views/cancha_views.xml',
        'views/reserva_views.xml',
        'views/portal_templates.xml',
        'views/assets_templates.xml',
        # 3. Menús (DESPUÉS de las vistas porque referencian las acciones)
        'views/menu_views.xml',
        # 4. Permisos de acceso (ahora los modelos ya existen)
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # 5. Finalmente datos de demostración
        'data/cancha_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}