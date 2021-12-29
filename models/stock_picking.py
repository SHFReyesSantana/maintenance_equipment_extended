from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    request_id = fields.Many2one(comodel_name='maintenance.request')

