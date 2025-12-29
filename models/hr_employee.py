# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    leave_recommender_id = fields.Many2one(
        'res.users',
        string='Leave Recommender',
        domain="[('share', '=', False)]",
        help='User who will recommend leave requests for this employee'
    )
    
    leave_forwarder_id = fields.Many2one(
        'res.users',
        string='Leave Forwarder',
        domain="[('share', '=', False)]",
        help='User who will forward leave requests after recommendation'
    )


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
    
    leave_recommender_id = fields.Many2one(
        'res.users',
        string='Leave Recommender',
        readonly=True
    )
    
    leave_forwarder_id = fields.Many2one(
        'res.users',
        string='Leave Forwarder',
        readonly=True
    )


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    leave_recommender_id = fields.Many2one(
        'res.users',
        string='Leave Recommender',
        related='employee_id.leave_recommender_id',
        readonly=False,
        related_sudo=False
    )
    
    leave_forwarder_id = fields.Many2one(
        'res.users',
        string='Leave Forwarder',
        related='employee_id.leave_forwarder_id',
        readonly=False,
        related_sudo=False
    )
    
    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['leave_recommender_id', 'leave_forwarder_id']
    
    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['leave_recommender_id', 'leave_forwarder_id']