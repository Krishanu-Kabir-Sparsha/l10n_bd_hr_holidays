# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeaveRefuseWizard(models.TransientModel):
    _name = 'hr.leave.refuse.wizard'
    _description = 'Leave Refuse Wizard'
    
    leave_id = fields.Many2one(
        'hr.leave', 
        string='Leave Request',
        required=True,
        readonly=True
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='leave_id.employee_id',
        readonly=True
    )
    
    refuse_reason = fields.Selection([
        ('insufficient_balance', 'Insufficient Leave Balance'),
        ('workload', 'Critical Workload/Project Deadline'),
        ('overlap', 'Overlapping with Other Leaves'),
        ('notice', 'Insufficient Notice Period'),
        ('document', 'Missing Supporting Documents'),
        ('policy', 'Policy Violation'),
        ('other', 'Other Reason'),
    ], string='Refuse Reason', required=True)
    
    refuse_notes = fields.Text(
        string='Additional Notes',
        help='Provide additional details for the refusal'
    )

    def action_refuse(self):
        """Refuse the leave request with reason"""
        self.ensure_one()
        
        if not self.leave_id:
            raise UserError(_('No leave request selected.'))
        
        reason_labels = dict(self._fields['refuse_reason'].selection)
        reason_text = reason_labels.get(self.refuse_reason, self.refuse_reason)
        
        message = _('Leave Request Refused - Reason: %s') % reason_text
        if self.refuse_notes:
            message += _(' - Notes: %s') % self.refuse_notes
        
        self.leave_id.action_refuse()
        self.leave_id.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )
        
        return {'type': 'ir.actions.act_window_close'}