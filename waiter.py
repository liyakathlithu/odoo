from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import time

class waiter(models.Model):
    _name = "waiter"
    _description = "Creating Orders from Customers"
    
    name = fields.Char(string="Name")
    state = fields.Selection([('order', 'Order'),
                            ('inprogress', 'In progress'),
                            ('readytoserve', 'Ready to Serve')], string="Status", default='order',tracking=True)
    cust_name = fields.Many2one('res.partner',string="Customer Name")
    ph_no=fields.Char(string="Phone number")
    line_ids = fields.One2many("waiter.line","product2_id", string="Orders")
    sequence=fields.Char(string="Sequence")
    product2_id = fields.Many2one('product.template', string="Products")
    is_food = fields.Boolean(string="Is Food?")
    food_count = fields.Integer(string="Liked food", compute='_compute_food_count')
    date = fields.Datetime("Order Date & Time", default=fields.Datetime.now)
    countdown_end = fields.Datetime('Preparation End Time', compute='_compute_countdown_end', store=True)
    remaining_time = fields.Char('Remaining Time Left', compute='_compute_remaining_time')

    def action_order(self):
        for rec in self:
            rec.state = 'order'
            
    def action_inprogress(self):
        if any(not line.product_id for line in self.line_ids):
            raise UserError("Please add products to all the order lines before proceeding.")
        for record in self:
            record.state = 'inprogress'
    
    def action_completed(self):
        for rec in self:
            rec.state = 'readytoserve'
        if rec.user_id:
                rec._send_notification()

    @api.depends('state')
    def _compute_countdown_end(self):
        for record in self:
            if record.state == 'inprogress':
                # Set countdown to 15 minutes from now when state is 'inprogress'
                record.countdown_end = fields.Datetime.now() + timedelta(minutes=1)
            else:
                record.countdown_end = False
                
    @api.depends('countdown_end')
    def _compute_remaining_time(self):
        for record in self:
            if record.countdown_end:
                time_left = record.countdown_end - fields.Datetime.now()
                if time_left.total_seconds() > 0:
                    mins = int(time_left.total_seconds() // 60)
                    secs = int(time_left.total_seconds() % 60)
                    record.remaining_time = f"{mins}m {secs}s"
                else:
                    record.remaining_time = "Time's up!"
            else:
                record.remaining_time = "No count"
            # self.send_notification_to_waiter()
    
    # def send_notification_to_waiter(self):
    #
    #     waiter_user = self.env['res.users']
    #     if waiter_user:
    #         # Notify using Odoo's built-in notification system
    #         waiter_user.partner_id.message_post(
    #             body="An order is ready to serve!",
    #             subject="Order Ready Notification",
    #             message_type="notification",
    #             subtype_xmlid="mail.mt_comment",  # Ensures it's a notification
    #         )
#sequence
    # @api.model_create_multi
    # def create(self, vals_list):
    #      for vals in vals_list:
    #          vals['sequence'] = self.env['ir.sequence'].next_by_code('sequence.waiter')
    #      return super(waiter, self).create(vals_list)
    

    @api.constrains('ph_no')
    def check_phno(self):
        for rec in self:
            if rec.ph_no:  # Only validate if ph_no is not empty
                if len(rec.ph_no) != 10 or not rec.ph_no.isdigit():
                    raise ValidationError("Phone number must be exactly 10 digits and numeric.")
                
    # @api.depends('line_ids.sub_total')
    # def _compute_order_total(self):
    #     for order in self:
    #         total = 0.0
    #         for line in order.line_ids:
    #             line_total = (line.sub_total)
    #             total += line_total
    #         order.order_total = total


    def schedule_action(self):
        print('_____________state_schedule_______________')
        records_to_update = self.search(['|', ('state', '=', 'readytoserve'), ('state', '=', 'inprogress')])
        records_to_update.write({
                                        'cust_name': False,      # Clear customer name
                                        'ph_no': False,          # Clear phone number
                                        'line_ids': [(5, 0, 0)], # Remove all order lines
                                        'product_ids': [(5, 0, 0)], # Clear Many2many field
                                        'state': 'order',        # Set state to draft for new order if applicable
                                        })

    def action_checkout(self):
        self.ensure_one()
    
        # Merge products in line_ids based on product_id and product_variant_id
        merged_products = {}
        for line in self.line_ids:
            product_key = (line.product_id.id, line.product_variant_id.id)
            if product_key in merged_products:
                merged_products[product_key]['product_uom_qty'] += line.quantity
            else:
                merged_products[product_key] = {
                                                'product_template_id': line.product_id.id,
                                                'product_id': line.product_variant_id.id,
                                                'name': line.desc,  # Product description
                                                'product_uom_qty': line.quantity,
                                                'price_unit': line.list_price,
                }
    
        # Create a new sale order record
        sale_order = self.env['sale.order'].create({
                                                    'partner_id': self.cust_name.id,
                                                    'date_order': fields.Date.today(),
                                                    'sale_ph_no': self.ph_no,
                                                    'table': self.name,
                                                    'waiter_id': self.env.user.name,
                                                    'order_line': [(0, 0, values) for values in merged_products.values()],
        })
    
        # Clear fields in the waiter model
        self.write({
                    'cust_name': False,       # Clear customer name
                    'ph_no': False,           # Clear phone number
                    'line_ids': [(5, 0, 0)],  # Remove all order lines
                    'state': 'order',         # Set state to 'order' for a new order
        })
    
        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Checkout Successful',
                'message': f"Sale Order has been created successfully!",
                'type': 'success',
                'sticky': False,
            },
        }



class waiterline(models.Model):
    _name = "waiter.line"
    _description = "waiter Line"


    product_category=fields.Char(string="Product Category")
    desc=fields.Char(string="Descrption")
    quantity=fields.Integer(string="Quantity",default=1)
    list_price=fields.Integer(string="Price")
    product2_id = fields.Many2one('waiter')
    product_id = fields.Many2one('product.template', string="Products")
    sub_total=fields.Integer(string="Sub Total", compute="_compute_sub_total", store=True)
    product_variant_id = fields.Many2one('product.product',string="Variants")
    served = fields.Boolean(string="Served", default=False)
    recently_prepared = fields.Boolean(string="Recently Prepared", default=False)
    
    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            rec.desc = rec.product_id.desc
            rec.list_price = rec.product_id.list_price
            rec.product_category = rec.product_id.product_category
            rec.product_variant_id = rec.product_id.product_variant_id

    @api.depends('product_id', 'quantity')
    def _compute_sub_total(self):
        for rec in self:
            if rec.product_id:
                rec.sub_total = rec.product_id.list_price * rec.quantity
            else:
                rec.sub_total = 0.0

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
