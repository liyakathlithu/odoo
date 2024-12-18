from odoo import api, fields, models, api
from odoo.exceptions import ValidationError
import re

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    email = fields.Char(string="Email")
    sale_ph_no=fields.Char(string="Phone number")
    food_count = fields.Integer(compute='_compute_food_count', string="Liked Foods")
    product_ids = fields.Many2many('product.template','two_one_rel','one_id','two_id', string="Liked Foods")
    sequence=fields.Char(string="Sequence")
    table=fields.Char(string="Table")
    waiter_id=fields.Char(string="Waiter ID")

    # def action_email(self):
    #     template=self.env.ref("restaurant.email_template_sale_order")
    #     for rec in self:
    #         template.send_mail(rec.id)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequence'] = self.env['ir.sequence'].next_by_code('sale.order')
        return super(SaleOrder, self).create(vals_list)

    
    def action_generate_xlsx_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/test/download_xlsx_report/%s' % self.id,
            'target': 'new',
        }
    
    @api.depends('product_ids')
    def _compute_food_count(self):
        for record in self:
            record.food_count = len(record.product_ids)
    
    @api.constrains('email')
    def check_email(self):
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        for rec in self:
            if rec.email and not re.match(email_pattern, rec.email):
                raise ValidationError("Email must contain alphabets, '@', and '.' in the format 'example@domain.com'.")

    @api.onchange('email')
    def _onchange_email_save_to_partner(self):
        if self.partner_id and self.email:
            self.partner_id.email = self.email
            
#smartbutton
    def action_view_sale_order(self):
        action = {
                'name': 'Sale_Order',
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.product_ids.ids)]
            }
        return action