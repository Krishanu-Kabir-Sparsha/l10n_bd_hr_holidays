# -*- coding: utf-8 -*-
{
    'name': 'Enhanced Leave Management',
    'version': '18.0.2.0.1',
    'category': 'Human Resources/Time Off',
    'summary': 'Enhanced Leave Management with Recommendation, Forward, Sandwich Policy & Carryover',
    'description': """
Enhanced Leave Management Module
================================
Key Features:
* Recommendation stage - Leave can be recommended before approval
* Forward stage - Leave can be forwarded to higher authority
* Configurable workflow per leave type
* Security groups for Recommender and Forwarder roles
* Sandwich leave policy - weekends/holidays between leaves count as leave
* Max days per year validation on allocations
* Minimum notice days validation on leave requests
* Carryover functionality with expiry
* Refuse with reason functionality
* Renamed "Time Off" to "Leaves" in menus
    """,
    'author': 'Kabir SE',
    'website': 'https://github.com/KabirSE',
    'license': 'LGPL-3',
    'depends': [
        'hr_holidays',
        'hr',
    ],
    'data': [
        # Security - must be first
        'security/hr_holidays_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_cron_data.xml',
        
        # Views
        'views/hr_leave_views.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_employee_views.xml',
        'views/res_users_views.xml',
        'views/hr_holidays_menus.xml',
        
        # Wizards
        'wizard/hr_leave_refuse_wizard_views.xml',
        'wizard/hr_leave_carryover_wizard_views.xml',
    ],
    'installable': True,
    'auto_install':  False,
    'application': False,
}