from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'maintenance.stage'

    color = fields.Integer()
