# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    # ========================================
    # SANDWICH LEAVE POLICY
    # ========================================
    
    l10n_bd_is_sandwich_leave = fields.Boolean(
        string='Apply Sandwich Rule',
        default=False,
        help='If enabled, weekends and public holidays falling between consecutive leave days '
             'will be counted as leave days. This applies when leaves connect across non-working days.'
    )
    
    # ========================================
    # LEAVE RULES (SIMPLIFIED)
    # ========================================
    
    l10n_bd_max_days_per_year = fields.Integer(
        string='Max Days Per Year',
        help='Maximum allowed days per year for this leave type'
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
    
    l10n_bd_notice_days = fields.Integer(
        string='Notice Days Required',
        default=0,
        help='Number of days advance notice required for this leave type'
    )