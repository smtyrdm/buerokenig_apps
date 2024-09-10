import logging
from odoo import models, exceptions, _, fields
from odoo.exceptions import UserError
import ast
import requests
import unicodedata
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class OrderFetchWizard(models.Model):
    _name = 'order.fetch.wizard'
    _description = 'Order Fetch Wizard'

    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')

    def fetch_orders(self):
        increment_id =''
        ir_data = {'message':'','path':'fetch_orders.py', 'func':'fetch_orders','line':''}



        """Fetch products"""
        OrderObj = self.env['sale.order']
        ProductObj = self.env['product.product']
        cr = self._cr
        # url = '/rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=status&' \
        #       'searchCriteria[filter_groups][0][filters][0][value]=canceled&' \
        #       'searchCriteria[filter_groups][0][filters][0][condition_type]=neq'

        date_start = self.date_start or False
        if not date_start:
            date_start = fields.Date.to_string(datetime.today() - timedelta(days=7))

        date_end = self.date_end or False
        if not date_end:
            date_end = fields.Date.to_string(datetime.today())



        _logger.warning(f"{date_start} - {date_end}")

        # url = '/rest/V1/orders?searchCriteria='

        url = (f'/rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=created_at&'
               f'searchCriteria[filter_groups][0][filters][0][value]={date_start}&'
               f'searchCriteria[filter_groups][0][filters][0][condition_type]=gteq&'
               f'searchCriteria[filter_groups][0][filters][1][field]=created_at&'
               f'searchCriteria[filter_groups][0][filters][1][value]={date_end}&'
               f'searchCriteria[filter_groups][0][filters][1][condition_type]=gteq')

        # url = f'/rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=created_at&' \
        #       f'searchCriteria[filter_groups][0][filters][0][value]={start_date}&' \
        #       f'searchCriteria[filter_groups][0][filters][0][condition_type]=gteq&' \
        #       f'searchCriteria[filter_groups][0][filters][1][field]=created_at&' \
        #       f'searchCriteria[filter_groups][0][filters][1][value]={end_date}&' \
        #       f'searchCriteria[filter_groups][0][filters][1][condition_type]=gteq'



        # url = (
        #     '/rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=increment_id&'
        #     'searchCriteria[filter_groups][0][filters][0][value]=000000551'
        # )
        type = 'GET'
        order_list = self.env['magento.connector'].magento_api_call(headers={},url=url,type=type)
        _logger.warning("==1")
        try:
            _logger.warning("==2")
            items = order_list['items']

            cr.execute("select magento_id from sale_order where magento_id is not null")
            orders = cr.fetchall()
            order_ids = [i[0] for i in orders] if orders else []

            cr.execute("select id from ir_model where model='sale.order'")
            order_model = cr.fetchone()

            if not order_model:
                return
            cr.execute("select name from ir_model_fields "
                       "where model_id=%s and required=True "
                       " and store=True",
                       (order_model[0],))
            res = cr.fetchall()
            fields_list = [i[0] for i in res if res] or []
            order_vals = OrderObj.default_get(fields_list)
            _logger.warning("==3")
            for i in items:
                _logger.warning("==4")
                increment_id = str(i['increment_id'])
                magento_ir_logs = self.env['ir.logging'].search([('line','=',increment_id)])
                if increment_id in magento_ir_logs.mapped('line'):
                    continue
                if str(i['increment_id']) not in order_ids:
                    _logger.info("fetch_orders")
                    res_contact, res_invoice, res_ship  = self.env['customer.fetch.wizard'].create_magento_customer(i)
                    order_vals['magento'] = True
                    order_vals['magento_id'], order_vals['magento_entity_id'] = str(i['increment_id']), i.get('entity_id','')
                    order_vals['partner_id'], order_vals['partner_invoice_id'], order_vals['partner_shipping_id'] = res_contact.id, res_invoice.id, res_ship.id
                    order_vals['magento_status'] = i.get('state') or i.get('status')
                    order_vals['date_order'] = i.get('created_at')

                    payment_method = self.env['magento.account.payment'].find_magento_payment(i)
                    incoterm = self.env['magento.account.incoterm'].find_magento_incoterm(i,'incoterm')
                    order_vals['payment_term_id'], order_vals['incoterm']  = payment_method.id,  incoterm.id

                    order_line = []
                    _logger.warning("==5")
                    for line in i['items']:
                        _logger.warning("==6")
                        if line.get('parent_item_id'): # product_type": "configurable" bağlı simple geliyor.
                            continue
                        sku = line['sku']
                        price = line.get('price',0.0) # bu alan her zaman vergi hariç gelir. yani excluding
                        prod_rec = ProductObj.search([('default_code', '=', sku)], limit=1)
                        if not sku or not prod_rec:
                            raise models.ValidationError(f"{sku} veya ürün yok. code_line:81")
                        ## <Taxes>
                        taxes = self.env['magento.account.taxes'].find_magento_catalog_taxes(i, line)
                        ## </Taxes>
                        temp = {
                            'product_id': prod_rec.id,
                            'product_uom_qty': line['qty_ordered'],
                            'price_unit': price,
                            'tax_id': [(6, 0, [taxes.id])],
                        }
                        order_line.append((0, 0, temp))

                    # Discount, Shipping service product
                    self.env['account.fetch.wizard'].find_magento_service_shipping(i, order_line)
                    self.env['account.fetch.wizard'].find_magento_service_discount(i, order_line)

                    order_vals['order_line'] = order_line
                    if 'message_follower_ids' in order_vals:
                        order_vals.pop('message_follower_ids')
                    order_vals['name'] = self.env['ir.sequence'].next_by_code('sale.order')

                    # odoo subtotal == magento subtotal
                    magento_subtotal = round(i['subtotal'] + i['shipping_amount'] + i.get('discount_excl_tax',0), 2)
                    odoo_subtotal = round(sum(item[2]['price_unit'] * item[2]['product_uom_qty'] for item in order_line),2)
                    if magento_subtotal != odoo_subtotal:
                        raise models.ValidationError(f" m != o ->{magento_subtotal} != {odoo_subtotal} -> ,code_line:106")
                    odoo_new = OrderObj.create(order_vals)
                    # odoo total == magento total
                    magento_total = i.get('total_paid',0) or i['total_due'] # paypal ile ödediyse total_due boş  geliyor.
                    odoo_total = round(odoo_new.amount_total,2)
                    if magento_total != odoo_total:
                        raise models.ValidationError(f"m != o ->{magento_total} != {odoo_total} -> code_line:112")
                    # engin: 03.09.2024: 3 döngü var, 2 si başarılı 1 başarız ise 2 oluşması için direk vt kayıt et.
                    self.env.cr.commit()

            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        except Exception as e:
            _logger.info("Exception occured %s", e)
            self.env['ir.logging'].magento_ir_logging(dict(ir_data, message=str(e), line=increment_id))
            raise exceptions.UserError(_("Error Occured orders %s") % e)

