# -*- coding: utf-8 -*-
{
    'name': "maintenance_equipment_extended",

    'summary': """
        Maintenance module expansion, locations and equipment parts added
    """,

    'description': """
        Maintenance module extension
    """,

    'author': "Reyes Hernando Santana Perez - inghernandosan@gmail.com",
    'website': "SHF S.A.S.",

    'category': 'Operations',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'dms',
        'maintenance',
        'purchase',
        'stock',
        'web_timeline',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_request_data.xml',
        'data/dms_storage_data.xml',
        'data/dms_directory_data.xml',
        'data/maintenance_product_product.xml',
        'report/maintenance_request_report.xml',
        'views/maintenance_location_view.xml',
        'views/maintenance_plan_view.xml',
        'views/maintenance_plan_part_view.xml',
        'views/maintenance_request_view.xml',
        'views/maintenance_stage_view.xml',
        'views/maintenance_task_view.xml',
        'views/maintenance_equipment_view.xml',
        'views/templates.xml',
    ],
}
