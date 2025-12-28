# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
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
        help='Minimum number of days in advance a leave request must be submitted.Set 0 for no restriction.'
    )
    
    l10n_bd_carryover_allowed = fields.Boolean(
        string='Allow Carryover',
        default=False,
        help='Allow unused leaves to be carried over to next year'
    )
    
    l10n_bd_carryover_max_days = fields.Integer(
        string='Max Carryover Days',
        default=0,
        help='Maximum days that can be carried over to next year.Set 0 for unlimited carryover.'
    )
    
    l10n_bd_carryover_expiry_months = fields.Integer(
        string='Carryover Expiry (Months)',
        default=3,
        help='Number of months after which carried over leaves expire.Set 0 for no expiry.'
    )

    def action_process_carryover(self):
        """Manual action to process carryover for this leave type"""
        self.ensure_one()
        return self.env['hr.leave.carryover.wizard'].process_carryover_for_type(self)