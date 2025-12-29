# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    # ========================================
    # WORKFLOW CONFIGURATION
    # ========================================
    
    l10n_bd_require_recommendation = fields.Boolean(
        string='Require Recommendation',
        default=False,
        help='If enabled, leave requests must be recommended before approval'
    )
    
    l10n_bd_require_forward = fields.Boolean(
        string='Require Forward',
        default=False,
        help='If enabled, leave requests must be forwarded after recommendation'
    )
    
    l10n_bd_recommender_ids = fields.Many2many(
        'res.users',
        'hr_leave_type_recommender_rel',
        'leave_type_id',
        'user_id',
        string='Notified Recommenders',
        help='Users who will be notified to recommend leaves of this type'
    )
    
    l10n_bd_forwarder_ids = fields.Many2many(
        'res.users',
        'hr_leave_type_forwarder_rel',
        'leave_type_id',
        'user_id',
        string='Notified Forwarders',
        help='Users who will be notified to forward leaves of this type'
    )
    
    # ========================================
    # ENHANCED LEAVE RULES
    # ========================================
    
    l10n_bd_is_sandwich_leave = fields.Boolean(
        string='Apply Sandwich Rule',
        default=False,
        help='If enabled, weekends and public holidays falling between consecutive leave days '
             'will be counted as leave days.'
    )
    
    l10n_bd_max_days_per_year = fields.Integer(
        string='Max Days Per Year',
        help='Maximum days that can be allocated per year for this leave type. Set 0 for unlimited.'
    )
    
    l10n_bd_notice_days = fields.Integer(
        string='Min Notice Days',
        default=0,
        help='Minimum number of days in advance a leave request must be submitted.'
    )
    
    l10n_bd_carryover_allowed = fields.Boolean(
        string='Allow Carryover',
        default=False,
        help='Allow unused leaves to be carried over to next year'
    )
    
    l10n_bd_carryover_max_days = fields.Integer(
        string='Max Carryover Days',
        default=0,
        help='Maximum days that can be carried over to next year.'
    )
    
    l10n_bd_carryover_expiry_months = fields.Integer(
        string='Carryover Expiry (Months)',
        default=3,
        help='Number of months after which carried over leaves expire.'
    )