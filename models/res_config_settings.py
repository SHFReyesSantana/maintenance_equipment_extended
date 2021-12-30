from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    maintenance_stage_id = fields.Many2one(comodel_name='maintenance.stage', string='Start Stage',
        default=lambda self: self.env['maintenance.stage'].search([('start_stage', '=', True)]))

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        stages = self.env['maintenance.stage'].search([])
        for stage in stages:
            if stage.id == self.maintenance_stage_id.id:
                stage.start_stage = True
            else:
                stage.start_stage = False
