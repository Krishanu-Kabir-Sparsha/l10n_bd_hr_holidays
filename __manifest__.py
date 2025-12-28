# -*- coding: utf-8 -*-
{
    'name': 'Enhanced Leave Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Simplified Leave Management with Sandwich Policy',
    'description': """
Enhanced Leave Management Module
================================
This module provides: 
- Simplified and enhanced UI/UX for leave management
- Consistent terminology: "Leaves" instead of "Time Off"
- Sandwich leave policy (like India localization)
- Enhanced dashboard and reporting
- Streamlined approval workflows
- Refuse with reason functionality

Key Features:
-------------
* Sandwich leave policy support
* Quick approval actions
* Refuse with reason wizard
* Leave category classification
* Enhanced list and form views
* Bengali translations support
    """,
    'author': 'Kabir SE',
    'website': 'https://github.com/KabirSE',
    'license': 'LGPL-3',
    'depends': [
        'hr_holidays',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/ir_cron_data.xml',
        
        # Views
        'views/hr_leave_views.xml',
        'views/hr_leave_type_views.xml',
        # 'views/hr_leave_allocation_views.xml',
        'views/hr_holidays_menus.xml',
        
        # Wizards
        'wizard/hr_leave_refuse_wizard_views.xml',
        'wizard/hr_leave_carryover_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}