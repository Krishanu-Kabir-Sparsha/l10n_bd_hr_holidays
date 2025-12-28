# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # ========================================
    # FIELDS
    # ========================================
    
    l10n_bd_contains_sandwich_leaves = fields.Boolean(
        string='Contains Sandwich Days',
        compute='_compute_l10n_bd_contains_sandwich_leaves',
        store=True,
        help='Indicates if sandwich rule is applied to this leave'
    )
    
    l10n_bd_is_sandwich_type = fields.Boolean(
        string='Is Sandwich Leave Type',
        related='holiday_status_id.l10n_bd_is_sandwich_leave',
        store=False,
        help='Technical field to check if leave type has sandwich rule'
    )

    # ========================================
    # COMPUTE METHODS
    # ========================================
    
    @api.depends('holiday_status_id', 'holiday_status_id.l10n_bd_is_sandwich_leave', 
                 'request_date_from', 'request_date_to', 'number_of_days')
    def _compute_l10n_bd_contains_sandwich_leaves(self):
        """Compute if sandwich rule applies to this leave"""
        for leave in self:
            leave.l10n_bd_contains_sandwich_leaves = (
                leave.holiday_status_id and 
                leave.holiday_status_id.l10n_bd_is_sandwich_leave and
                leave.request_date_from and 
                leave.request_date_to
            )

    # ========================================
    # VALIDATION - NOTICE DAYS
    # ========================================
    
    @api.constrains('request_date_from', 'holiday_status_id')
    def _check_notice_days(self):
        """Validate that leave request meets minimum notice days requirement"""
        for leave in self:
            if not leave.holiday_status_id or not leave.request_date_from:
                continue
            
            notice_days = leave.holiday_status_id.l10n_bd_notice_days
            if not notice_days or notice_days <= 0:
                continue
            
            # Calculate days between today and leave start date
            today = date.today()
            leave_start = leave.request_date_from
            
            if isinstance(leave_start, datetime):
                leave_start = leave_start.date()
            
            days_advance = (leave_start - today).days
            
            if days_advance < notice_days:
                raise ValidationError(
                    _('Leave type "%(leave_type)s" requires at least %(notice)s days advance notice.'
                      'Your leave starts in %(days)s days.') % {
                        'leave_type': leave.holiday_status_id.name,
                        'notice': notice_days,
                        'days': max(0, days_advance),
                    }
                )

    # ========================================
    # SANDWICH LEAVE LOGIC
    # ========================================
    
    def _l10n_bd_apply_sandwich_rule(self, public_holidays, employee_leaves):
        """Apply sandwich leave rule"""
        self.ensure_one()
        
        if not self.request_date_from or not self.request_date_to:
            return 0
        
        date_from = self.request_date_from
        date_to = self.request_date_to
        
        if date_from > date_to: 
            return 0
            
        total_leaves = (date_to - date_from).days + 1
        
        calendar = self.resource_calendar_id
        if not calendar:
            return total_leaves
        
        def is_non_working_day(check_date):
            try:
                if not calendar._works_on_date(check_date):
                    return True
                for holiday in public_holidays:
                    holiday_from = holiday.get('date_from')
                    holiday_to = holiday.get('date_to')
                    if holiday_from and holiday_to:
                        if isinstance(holiday_from, datetime):
                            holiday_from = holiday_from.date()
                        if isinstance(holiday_to, datetime):
                            holiday_to = holiday_to.date()
                        if holiday_from <= check_date <= holiday_to:
                            return True
                return False
            except Exception:
                return False
        
        def count_sandwich_days(start_date, direction):
            days_count = 0
            max_check = 7
            
            try:
                current_date = start_date + timedelta(days=direction)
                checked = 0
                
                while checked < max_check:
                    if not is_non_working_day(current_date):
                        break
                    
                    days_count += 1
                    checked += 1
                    current_date = current_date + timedelta(days=direction)
                
                if days_count > 0:
                    for leave in employee_leaves:
                        leave_from = leave.get('request_date_from')
                        leave_to = leave.get('request_date_to')
                        if leave_from and leave_to: 
                            if leave_from <= current_date <= leave_to: 
                                return days_count
                    return 0
                    
                return 0
            except Exception: 
                return 0
        
        sandwich_before = count_sandwich_days(date_from, -1)
        sandwich_after = count_sandwich_days(date_to, 1)
        total_leaves += sandwich_before + sandwich_after
        
        return total_leaves
    
    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """Override to apply sandwich rule if enabled on leave type"""
        result = super()._get_durations(check_leave_type, resource_calendar)
        
        sandwich_leaves = self.filtered(
            lambda l: l.holiday_status_id and 
            hasattr(l.holiday_status_id, 'l10n_bd_is_sandwich_leave') and 
            l.holiday_status_id.l10n_bd_is_sandwich_leave and
            l.request_date_from and l.request_date_to
        )
        
        if not sandwich_leaves:
            return result
        
        try:
            public_holidays = self.env['resource.calendar.leaves'].search_read([
                ('resource_id', '=', False),
                ('company_id', 'in', sandwich_leaves.company_id.ids),
            ], ['date_from', 'date_to'])
        except Exception:
            public_holidays = []
        
        leaves_by_employee = {}
        try:
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
        except Exception:
            pass
        
        for leave in sandwich_leaves:
            if leave.id in result:
                days, hours = result[leave.id]
                emp_leaves = leaves_by_employee.get(leave.employee_id.id, [])
                try:
                    updated_days = leave._l10n_bd_apply_sandwich_rule(public_holidays, emp_leaves)
                    if updated_days and updated_days != days:
                        result[leave.id] = (updated_days, hours)
                except Exception: 
                    pass
        
        return result

    # ========================================
    # STRICT APPROVAL LOGIC
    # ========================================
    
    def _check_approval_rights(self):
        """Check if current user has rights to approve this leave"""
        self.ensure_one()
        current_user = self.env.user
        
        if self.env.is_superuser():
            return True
        
        leave_manager = self.employee_id.leave_manager_id
        responsible_users = self.holiday_status_id.responsible_ids
        validation_type = self.holiday_status_id.leave_validation_type
        
        if validation_type == 'manager':
            if current_user == leave_manager:
                return True
            raise AccessError(
                _('Only %s (the Leave Approver) can approve this leave request.') % 
                (leave_manager.name if leave_manager else 'the assigned manager')
            )
        
        if validation_type == 'hr': 
            if current_user in responsible_users:
                return True
            raise AccessError(
                _('Only the HR Responsible users configured on the leave type can approve this request.')
            )
        
        if validation_type == 'both': 
            if self.state == 'confirm': 
                if current_user == leave_manager:
                    return True
                raise AccessError(
                    _('First approval must be done by %s (the Leave Approver).') % 
                    (leave_manager.name if leave_manager else 'the assigned manager')
                )
            elif self.state == 'validate1':
                if current_user in responsible_users:
                    return True
                raise AccessError(
                    _('Second approval must be done by the HR Responsible users configured on the leave type.')
                )
        
        if validation_type == 'no_validation':
            return True
        
        return False
    
    def action_approve(self, check_state=True):
        """Override to enforce strict approval rights"""
        for leave in self:
            leave._check_approval_rights()
        return super().action_approve(check_state)
    
    def action_validate(self, check_state=True):
        """Override to enforce strict validation rights"""
        for leave in self:
            leave._check_approval_rights()
        return super().action_validate(check_state)
    
    def action_refuse(self):
        """Override to enforce strict refusal rights"""
        for leave in self:
            leave._check_approval_rights()
        return super().action_refuse()

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