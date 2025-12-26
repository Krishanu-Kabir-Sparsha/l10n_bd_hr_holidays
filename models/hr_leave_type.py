# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    # ========================================
    # LEAVE CATEGORY & CLASSIFICATION
    # ========================================
    
    l10n_bd_leave_category = fields.Selection([
        ('annual', 'Annual Leave'),
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('earned', 'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('festival', 'Festival Leave'),
        ('compensatory', 'Compensatory Off'),
        ('unpaid', 'Leave Without Pay'),
        ('other', 'Other'),
    ], string='Leave Category', default='other',
       help='Leave categorization for reporting and filtering')
    
    # ========================================
    # SANDWICH LEAVE POLICY
    # ========================================
    
    l10n_bd_is_sandwich_leave = fields.Boolean(
        string='Apply Sandwich Rule',
        default=False,
        help='If enabled, weekends and public holidays between leave days will be counted as leave days.'
    )
    
    # ========================================
    # LEAVE RULES
    # ========================================
    
    l10n_bd_max_days_per_year = fields.Integer(
        string='Max Days Per Year',
        help='Maximum allowed days per year'
    )
    
    l10n_bd_carryover_allowed = fields.Boolean(
        string='Carryover Allowed',
        default=False,
        help='Whether unused leaves can be carried over to next year'
    )
    
    l10n_bd_carryover_max_days = fields.Integer(
        string='Max Carryover Days',
        help='Maximum days that can be carried over'
    )
    
    l10n_bd_encashment_allowed = fields.Boolean(
        string='Encashment Allowed',
        default=False,
        help='Whether unused leaves can be encashed'
    )
    
    l10n_bd_min_service_required = fields.Integer(
        string='Min Service (Months)',
        help='Minimum months of service required to avail this leave'
    )
    
    l10n_bd_notice_days = fields.Integer(
        string='Notice Days Required',
        default=0,
        help='Number of days advance notice required'
    )