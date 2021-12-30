from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'maintenance.stage'

    color = fields.Integer()
    start_stage = fields.Boolean(string='Start Stage', readonly=True)

