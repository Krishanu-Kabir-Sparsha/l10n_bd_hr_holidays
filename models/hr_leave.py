# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # ========================================
    # OVERRIDE STATE FIELD TO ADD NEW STATES
    # ========================================
    
    state = fields.Selection(
        selection_add=[
            ('recommend', 'Recommended'),
            ('forward', 'Forwarded'),
        ],
        ondelete={
            'recommend': 'set default',
            'forward': 'set default',
        }
    )
    
    # ========================================
    # NEW FIELDS FOR WORKFLOW
    # ========================================
    
    l10n_bd_recommended_by = fields.Many2one(
        'res.users',
        string='Recommended By',
        readonly=True,
        copy=False
    )
    
    l10n_bd_recommended_date = fields.Datetime(
        string='Recommendation Date',
        readonly=True,
        copy=False
    )
    
    l10n_bd_forwarded_by = fields.Many2one(
        'res.users',
        string='Forwarded By',
        readonly=True,
        copy=False
    )
    
    l10n_bd_forwarded_date = fields.Datetime(
        string='Forward Date',
        readonly=True,
        copy=False
    )
    
    l10n_bd_can_recommend = fields.Boolean(
        string='Can Recommend',
        compute='_compute_l10n_bd_can_recommend',
        store=False
    )
    
    l10n_bd_can_forward = fields.Boolean(
        string='Can Forward',
        compute='_compute_l10n_bd_can_forward',
        store=False
    )
    
    l10n_bd_can_approve_leave = fields.Boolean(
        string='Can Approve Leave',
        compute='_compute_l10n_bd_can_approve_leave',
        store=False
    )
    
    l10n_bd_show_recommend_button = fields.Boolean(
        string='Show Recommend Button',
        compute='_compute_l10n_bd_show_buttons',
        store=False
    )
    
    l10n_bd_show_forward_button = fields.Boolean(
        string='Show Forward Button',
        compute='_compute_l10n_bd_show_buttons',
        store=False
    )
    
    l10n_bd_show_skip_forward_button = fields.Boolean(
        string='Show Skip Forward Button',
        compute='_compute_l10n_bd_show_buttons',
        store=False
    )
    
    l10n_bd_show_approve_button = fields.Boolean(
        string='Show Approve Button',
        compute='_compute_l10n_bd_show_buttons',
        store=False
    )
    
    # ========================================
    # EXISTING ENHANCED FIELDS
    # ========================================
    
    l10n_bd_contains_sandwich_leaves = fields.Boolean(
        string='Contains Sandwich Days',
        compute='_compute_l10n_bd_contains_sandwich_leaves',
        store=True
    )
    
    l10n_bd_is_sandwich_type = fields.Boolean(
        string='Is Sandwich Leave Type',
        related='holiday_status_id.l10n_bd_is_sandwich_leave',
        store=False
    )

    # ========================================
    # STRICT ACCESS CONTROL - HELPER METHODS
    # ========================================
    
    def _is_assigned_recommender(self):
        """Check if current user is an assigned recommender for this leave"""
        if not self or not self.id:
            return False
        current_user = self.env.user
        
        # Check if user is the employee's designated recommender
        if self.employee_id and self.employee_id.leave_recommender_id == current_user: 
            return True
        
        # Check if user is in leave type's designated recommenders
        if self.holiday_status_id and current_user in self.holiday_status_id.l10n_bd_recommender_ids:
            return True
        
        return False
    
    def _is_assigned_forwarder(self):
        """Check if current user is an assigned forwarder for this leave"""
        if not self or not self.id:
            return False
        current_user = self.env.user
        
        # Check if user is the employee's designated forwarder
        if self.employee_id and self.employee_id.leave_forwarder_id == current_user:
            return True
        
        # Check if user is in leave type's designated forwarders
        if self.holiday_status_id and current_user in self.holiday_status_id.l10n_bd_forwarder_ids:
            return True
        
        return False
    
    def _is_assigned_approver(self):
        """Check if current user is an assigned approver for this leave"""
        if not self or not self.id:
            return False
        current_user = self.env.user
        
        # Check if user is the employee's designated leave manager/approver
        if self.employee_id and self.employee_id.leave_manager_id == current_user:
            return True
        
        return False
    
    def _is_assigned_validator(self):
        """Check if current user is an assigned validator (HR Officer) for this leave"""
        if not self or not self.id:
            return False
        current_user = self.env.user
        
        # Check if user is in leave type's responsible/HR officers
        if self.holiday_status_id and current_user in self.holiday_status_id.responsible_ids:
            return True
        
        return False

    # ========================================
    # COMPUTE METHODS
    # ========================================

    @api.depends('state', 'employee_id', 'holiday_status_id', 'employee_id.leave_recommender_id')
    def _compute_l10n_bd_can_recommend(self):
        """Check if current user can recommend this leave - STRICT"""
        for leave in self:
            try:
                leave.l10n_bd_can_recommend = leave._is_assigned_recommender()
            except Exception:
                leave.l10n_bd_can_recommend = False
    
    @api.depends('state', 'employee_id', 'holiday_status_id', 'employee_id.leave_forwarder_id')
    def _compute_l10n_bd_can_forward(self):
        """Check if current user can forward this leave - STRICT"""
        for leave in self:
            try:
                leave.l10n_bd_can_forward = leave._is_assigned_forwarder()
            except Exception: 
                leave.l10n_bd_can_forward = False
    
    @api.depends('state', 'employee_id', 'holiday_status_id', 'employee_id.leave_manager_id')
    def _compute_l10n_bd_can_approve_leave(self):
        """Check if current user can approve this leave - STRICT"""
        for leave in self:
            try:
                if not leave.holiday_status_id:
                    leave.l10n_bd_can_approve_leave = False
                    continue
                    
                validation_type = leave.holiday_status_id.leave_validation_type
                
                can_approve = False
                
                if validation_type == 'no_validation':
                    can_approve = True
                elif validation_type == 'manager':
                    can_approve = leave._is_assigned_approver()
                elif validation_type == 'hr': 
                    can_approve = leave._is_assigned_validator()
                elif validation_type == 'both':
                    if leave.state in ['confirm', 'recommend', 'forward']:
                        can_approve = leave._is_assigned_approver()
                    elif leave.state == 'validate1':
                        can_approve = leave._is_assigned_validator()
                
                leave.l10n_bd_can_approve_leave = can_approve
            except Exception: 
                leave.l10n_bd_can_approve_leave = False
    
    @api.depends('state', 'holiday_status_id', 'l10n_bd_can_recommend', 'l10n_bd_can_forward', 'l10n_bd_can_approve_leave')
    def _compute_l10n_bd_show_buttons(self):
        """Compute which buttons to show based on strict access"""
        for leave in self:
            try:
                # Show Recommend button
                show_recommend = (
                    leave.state == 'confirm' and
                    leave.holiday_status_id and
                    leave.holiday_status_id.l10n_bd_require_recommendation and
                    leave.l10n_bd_can_recommend
                )
                leave.l10n_bd_show_recommend_button = show_recommend
                
                # Show Forward button
                show_forward = (
                    leave.state == 'recommend' and
                    leave.holiday_status_id and
                    leave.holiday_status_id.l10n_bd_require_forward and
                    leave.l10n_bd_can_forward
                )
                leave.l10n_bd_show_forward_button = show_forward
                
                # Show Skip Forward button
                leave.l10n_bd_show_skip_forward_button = show_forward
                
                # Show Approve button
                leave.l10n_bd_show_approve_button = (
                    leave.state == 'forward' and
                    leave.l10n_bd_can_approve_leave
                )
            except Exception:
                leave.l10n_bd_show_recommend_button = False
                leave.l10n_bd_show_forward_button = False
                leave.l10n_bd_show_skip_forward_button = False
                leave.l10n_bd_show_approve_button = False
    
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
    # STRICT ACCESS CONTROL - CHECK METHODS
    # ========================================
    
    def _check_recommend_rights(self):
        """Strictly check if current user can recommend - raises error if not"""
        self.ensure_one()
        
        if not self._is_assigned_recommender():
            recommender = self.employee_id.leave_recommender_id if self.employee_id else False
            type_recommenders = self.holiday_status_id.l10n_bd_recommender_ids if self.holiday_status_id else False
            
            msg = _('You are not authorized to recommend this leave request.\n\n')
            if recommender:
                msg += _('Assigned Recommender: %s\n') % recommender.name
            if type_recommenders: 
                msg += _('Leave Type Recommenders: %s') % ', '.join(type_recommenders.mapped('name'))
            if not recommender and not type_recommenders:
                msg += _('No recommender has been assigned for this employee or leave type.')
            
            raise AccessError(msg)
        return True
    
    def _check_forward_rights(self):
        """Strictly check if current user can forward - raises error if not"""
        self.ensure_one()
        
        if not self._is_assigned_forwarder():
            forwarder = self.employee_id.leave_forwarder_id if self.employee_id else False
            type_forwarders = self.holiday_status_id.l10n_bd_forwarder_ids if self.holiday_status_id else False
            
            msg = _('You are not authorized to forward this leave request.\n\n')
            if forwarder:
                msg += _('Assigned Forwarder: %s\n') % forwarder.name
            if type_forwarders:
                msg += _('Leave Type Forwarders: %s') % ', '.join(type_forwarders.mapped('name'))
            if not forwarder and not type_forwarders:
                msg += _('No forwarder has been assigned for this employee or leave type.')
            
            raise AccessError(msg)
        return True
    
    def _check_approval_rights_strict(self):
        """Strictly check if current user can approve - raises error if not"""
        self.ensure_one()
        
        if not self.holiday_status_id:
            return True
            
        validation_type = self.holiday_status_id.leave_validation_type
        
        if validation_type == 'no_validation': 
            return True
        
        if validation_type == 'manager':
            if not self._is_assigned_approver():
                approver = self.employee_id.leave_manager_id if self.employee_id else False
                msg = _('You are not authorized to approve this leave request.\n\n')
                msg += _('Only the assigned Leave Approver can approve.\n')
                if approver: 
                    msg += _('Assigned Approver: %s') % approver.name
                else:
                    msg += _('No approver has been assigned for this employee.')
                raise AccessError(msg)
        
        elif validation_type == 'hr': 
            if not self._is_assigned_validator():
                validators = self.holiday_status_id.responsible_ids if self.holiday_status_id else False
                msg = _('You are not authorized to approve this leave request.\n\n')
                msg += _('Only the HR Officers configured on the leave type can approve.\n')
                if validators:
                    msg += _('Authorized Officers: %s') % ', '.join(validators.mapped('name'))
                else:
                    msg += _('No HR Officers have been configured for this leave type.')
                raise AccessError(msg)
        
        elif validation_type == 'both':
            if self.state in ['confirm', 'recommend', 'forward']:
                if not self._is_assigned_approver():
                    approver = self.employee_id.leave_manager_id if self.employee_id else False
                    msg = _('You are not authorized to approve this leave request.\n\n')
                    msg += _('First approval must be done by the assigned Leave Approver.\n')
                    if approver:
                        msg += _('Assigned Approver: %s') % approver.name
                    else:
                        msg += _('No approver has been assigned for this employee.')
                    raise AccessError(msg)
            elif self.state == 'validate1':
                if not self._is_assigned_validator():
                    validators = self.holiday_status_id.responsible_ids if self.holiday_status_id else False
                    msg = _('You are not authorized to validate this leave request.\n\n')
                    msg += _('Second approval (validation) must be done by HR Officers.\n')
                    if validators:
                        msg += _('Authorized Officers: %s') % ', '.join(validators.mapped('name'))
                    else: 
                        msg += _('No HR Officers have been configured for this leave type.')
                    raise AccessError(msg)
        
        return True

    # ========================================
    # ACTION METHODS - RECOMMEND & FORWARD
    # ========================================
    
    def action_recommend(self):
        """Recommend the leave request - STRICT ACCESS"""
        for leave in self:
            if leave.state != 'confirm': 
                raise UserError(_('Only submitted leave requests can be recommended.'))
            
            if not leave.holiday_status_id.l10n_bd_require_recommendation:
                raise UserError(_('This leave type does not require recommendation.'))
            
            # STRICT: Check if user is authorized
            leave._check_recommend_rights()
            
            leave.write({
                'state': 'recommend',
                'l10n_bd_recommended_by': self.env.user.id,
                'l10n_bd_recommended_date': fields.Datetime.now(),
            })
            
            leave.message_post(
                body=_('Leave request recommended by %s') % self.env.user.name,
                message_type='notification'
            )
            
            # If forward is not required, move directly to forward state
            if not leave.holiday_status_id.l10n_bd_require_forward:
                leave.write({'state': 'forward'})
                leave.message_post(
                    body=_('Forward stage skipped (not required for this leave type)'),
                    message_type='notification'
                )
        
        return True
    
    def action_forward(self):
        """Forward the leave request - STRICT ACCESS"""
        for leave in self:
            if leave.state != 'recommend':
                raise UserError(_('Only recommended leave requests can be forwarded.'))
            
            # STRICT: Check if user is authorized
            leave._check_forward_rights()
            
            leave.write({
                'state': 'forward',
                'l10n_bd_forwarded_by': self.env.user.id,
                'l10n_bd_forwarded_date': fields.Datetime.now(),
            })
            
            leave.message_post(
                body=_('Leave request forwarded by %s') % self.env.user.name,
                message_type='notification'
            )
        
        return True
    
    def action_skip_forward(self):
        """Skip forward stage - STRICT ACCESS (only forwarders can skip)"""
        for leave in self:
            if leave.state != 'recommend':
                raise UserError(_('Only recommended leave requests can skip forward.'))
            
            # STRICT: Only forwarders can skip forward
            leave._check_forward_rights()
            
            leave.write({
                'state': 'forward',
                'l10n_bd_forwarded_by': self.env.user.id,
                'l10n_bd_forwarded_date': fields.Datetime.now(),
            })
            
            leave.message_post(
                body=_('Forward stage skipped by %s') % self.env.user.name,
                message_type='notification'
            )
        
        return True

    # ========================================
    # OVERRIDE ACTION METHODS - STRICT ACCESS
    # ========================================
    
    def action_approve(self, check_state=True):
        """Override to enforce STRICT approval rights"""
        for leave in self:
            # Check workflow stages first
            if (leave.holiday_status_id.l10n_bd_require_recommendation and 
                leave.state == 'confirm'):
                raise UserError(_('This leave requires recommendation before approval.'))
            
            if (leave.holiday_status_id.l10n_bd_require_forward and 
                leave.state == 'recommend'):
                raise UserError(_('This leave requires forwarding before approval.'))
            
            # STRICT: Check if user is authorized to approve
            leave._check_approval_rights_strict()
            
            # If state is 'forward', change to 'confirm' for parent method
            if leave.state == 'forward':
                leave.write({'state': 'confirm'})
        
        return super().action_approve(check_state)
    
    def action_validate(self, check_state=True):
        """Override to enforce STRICT validation rights"""
        for leave in self:
            # STRICT: Check if user is authorized to validate
            leave._check_approval_rights_strict()
        
        return super().action_validate(check_state)
    
    def action_refuse(self):
        """Override to enforce STRICT refusal rights"""
        for leave in self:
            # For refusal, check based on current state
            can_refuse = False
            
            if leave.state == 'confirm':
                can_refuse = (leave._is_assigned_recommender() or 
                             leave._is_assigned_approver() or 
                             leave._is_assigned_validator())
            elif leave.state == 'recommend':
                can_refuse = (leave._is_assigned_forwarder() or 
                             leave._is_assigned_approver() or 
                             leave._is_assigned_validator())
            elif leave.state in ['forward', 'validate1']: 
                can_refuse = (leave._is_assigned_approver() or 
                             leave._is_assigned_validator())
            else:
                can_refuse = True  # Allow for other states
            
            if not can_refuse:
                raise AccessError(_('You are not authorized to refuse this leave request.'))
        
        return super().action_refuse()

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
            
            today = date.today()
            leave_start = leave.request_date_from
            
            if isinstance(leave_start, datetime):
                leave_start = leave_start.date()
            
            days_advance = (leave_start - today).days
            
            if days_advance < notice_days:
                raise ValidationError(
                    _('Leave type "%(leave_type)s" requires at least %(notice)s days advance notice. '
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
    # OTHER ACTION METHODS
    # ========================================
    
    def action_approve_quick(self):
        """Quick approve action - STRICT ACCESS"""
        self.ensure_one()
        if self.state not in ['confirm', 'recommend', 'forward']:
            raise UserError(_('This leave cannot be approved in its current state.'))
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