from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    user_points = fields.Integer(string="User Points")
