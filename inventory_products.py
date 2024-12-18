from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    desc = fields.Char(string="Descrption")
    product_category = fields.Selection([
                                            ('veg', 'Veg'),
                                            ('nonveg', 'Non Veg'),
                                            ('beverage', 'Beverages'),
                                            ('breads', 'Breads')
                                        ], string="Product Category", required=True)
    product_id = fields.Many2one('waiter', string="Products")
    product2_id = fields.Many2one('product.template', string="Products")
    quantity = fields.Integer(string="Quantity", default=1)
    is_food = fields.Boolean(string="Is Food?")
            
