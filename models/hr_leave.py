# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # ========================================
    # FIELDS
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
    ], string='Leave Category', compute='_compute_leave_category', store=True,
       help='Leave categorization')
    
    l10n_bd_contains_sandwich_leaves = fields.Boolean(
        string='Contains Sandwich Days',
        compute='_compute_sandwich_info',
        store=True,
        help='Indicates if sandwich rule is applied to this leave'
    )

    # ========================================
    # COMPUTE METHODS
    # ========================================
    
    @api.depends('holiday_status_id', 'holiday_status_id.l10n_bd_leave_category')
    def _compute_leave_category(self):
        for leave in self:
            if leave.holiday_status_id and hasattr(leave.holiday_status_id, 'l10n_bd_leave_category') and leave.holiday_status_id.l10n_bd_leave_category: 
                leave.l10n_bd_leave_category = leave.holiday_status_id.l10n_bd_leave_category
            else: 
                leave.l10n_bd_leave_category = 'other'
    
    @api.depends('request_date_from', 'request_date_to', 'holiday_status_id.l10n_bd_is_sandwich_leave')
    def _compute_sandwich_info(self):
        for leave in self: 
            leave.l10n_bd_contains_sandwich_leaves = False
            if leave.holiday_status_id and hasattr(leave.holiday_status_id, 'l10n_bd_is_sandwich_leave'):
                if leave.holiday_status_id.l10n_bd_is_sandwich_leave and leave.request_date_from and leave.request_date_to:
                    leave.l10n_bd_contains_sandwich_leaves = True

    # ========================================
    # SANDWICH LEAVE LOGIC
    # ========================================
    
    def _l10n_bd_apply_sandwich_rule(self, public_holidays, employee_leaves):
        """
        Apply sandwich leave rule - if leave is adjacent to weekends/holidays,
        those days are counted as leave too.
        """
        self.ensure_one()
        if not self.request_date_from or not self.request_date_to: 
            return self.number_of_days
        
        date_from = self.request_date_from
        date_to = self.request_date_to
        total_leaves = (self.request_date_to - self.request_date_from).days + 1
        
        calendar = self.resource_calendar_id
        if not calendar:
            return total_leaves
        
        def is_non_working_day(date):
            """Check if date is a non-working day (weekend or public holiday)"""
            # Check if it's a working day according to calendar
            if not calendar._works_on_date(date):
                return True
            # Check if it's a public holiday
            for holiday in public_holidays:
                holiday_from = holiday.get('date_from')
                holiday_to = holiday.get('date_to')
                if holiday_from and holiday_to: 
                    if isinstance(holiday_from, datetime):
                        holiday_from = holiday_from.date()
                    if isinstance(holiday_to, datetime):
                        holiday_to = holiday_to.date()
                    if holiday_from <= date <= holiday_to:
                        return True
            return False
        
        def count_sandwich_days(date, direction):
            """Count consecutive non-working days in given direction"""
            current_date = date + timedelta(days=direction)
            days_count = 0
            while is_non_working_day(current_date):
                days_count += 1
                current_date += timedelta(days=direction)
            # Check if another leave starts/ends on current_date
            for leave in employee_leaves:
                leave_from = leave.get('request_date_from')
                leave_to = leave.get('request_date_to')
                if leave_from and leave_to:
                    if leave_from <= current_date <= leave_to:
                        return days_count
            return 0
        
        # Add sandwich days before and after
        total_leaves += count_sandwich_days(date_from, -1)
        total_leaves += count_sandwich_days(date_to, 1)
        
        return total_leaves
    
    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """Override to apply sandwich rule if enabled on leave type"""
        result = super()._get_durations(check_leave_type, resource_calendar)
        
        # Filter leaves with sandwich rule enabled
        sandwich_leaves = self.filtered(
            lambda l: l.holiday_status_id and 
            hasattr(l.holiday_status_id, 'l10n_bd_is_sandwich_leave') and 
            l.holiday_status_id.l10n_bd_is_sandwich_leave
        )
        
        if not sandwich_leaves: 
            return result
        
        # Get public holidays
        public_holidays = self.env['resource.calendar.leaves'].search_read([
            ('resource_id', '=', False),
            ('company_id', 'in', sandwich_leaves.company_id.ids),
        ], ['date_from', 'date_to'])
        
        # Get other employee leaves
        leaves_by_employee = {}
        if sandwich_leaves:
            other_leaves = self.env['hr.leave'].search_read([
                ('id', 'not in', self.ids),
                ('employee_id', 'in', sandwich_leaves.employee_id.ids),
                ('state', 'not in', ['cancel', 'refuse']),
            ], ['employee_id', 'request_date_from', 'request_date_to'])
            
            for leave_data in other_leaves: 
                emp_id = leave_data['employee_id'][0] if leave_data['employee_id'] else False
                if emp_id: 
                    if emp_id not in leaves_by_employee: 
                        leaves_by_employee[emp_id] = []
                    leaves_by_employee[emp_id].append(leave_data)
        
        # Apply sandwich rule
        for leave in sandwich_leaves:
            if leave.id in result:
                days, hours = result[leave.id]
                emp_leaves = leaves_by_employee.get(leave.employee_id.id, [])
                updated_days = leave._l10n_bd_apply_sandwich_rule(public_holidays, emp_leaves)
                if updated_days != days:
                    result[leave.id] = (updated_days, hours)
                    if leave.state not in ['validate', 'validate1']: 
                        leave.l10n_bd_contains_sandwich_leaves = True
        
        return result

    # ========================================
    # ACTION METHODS
    # ========================================
    
    def action_approve_quick(self):
        """Quick approve action"""
        self.ensure_one()
        if self.state != 'confirm':
            raise UserError(_('Only pending leaves can be approved.'))
        return self.action_approve()
    
    def action_refuse_with_reason(self):
        """Open wizard to refuse with reason"""
        self.ensure_one()
        return {
            'name': _('Refuse Leave Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_leave_id': self.id,
                'default_employee_id': self.employee_id.id,
            }
        }