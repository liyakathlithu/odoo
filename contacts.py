from odoo import api, fields, models


class respartner(models.Model):
    _inherit = "res.partner"
    
    remarks=fields.Char(string="Remarks")
    
    def schedule_email_loyal(self):
        customers = self.env['res.partner'].search([('email', '!=', False), ('active', '=', True)])
        template=self.env.ref("restaurant.daily_email_template")
        
        for customer in customers:
            template.send_mail(customer.id, force_send=True)
