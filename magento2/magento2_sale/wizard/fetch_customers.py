import logging

from odoo import models, exceptions, _

_logger = logging.getLogger(__name__)


class CustomerFetchWizard(models.Model):
    _name = 'customer.fetch.wizard'
    _inherit = 'order.fetch.wizard'
    _description = 'Customer Fetch Wizard'

    def create_magento_customer(self, item):
        # shipp vat olsa bile odoo ship kayıt edilemiyor.
        # bill vat yok, ship de var varsa ve içerik aynı ise bill.vat = ship.vat
        magento_store = self.env['magento.stores'].search([('store_id', '=', item.get('store_id'))], limit=1)

        if not magento_store or magento_store and not magento_store.lang_id.code:
            raise models.ValidationError(f"Stores/Magento Store: store_id: {item.get('store_id')} not! or lang_id not!")

        lang = magento_store.lang_id.code
        bill = item.get("billing_address", {})
        ship = item.get("extension_attributes", {}).get("shipping_assignments", [{}])[0].get("shipping", {}).get("address", {})
        if not bill:
            raise models.ValidationError("create_magento_customer | not bill")

        bill_list = self.get_address_list(bill)
        bill_list['lang'] = lang
        # Billing
        res_bill, bill_list = self.get_billing(bill_list, item)
        if not res_bill:
            raise models.ValidationError("create_magento_customer | not res_bill")
        # Contact
        res_contact = self.get_billing_contact(bill, lang, res_bill)
        # Shipping
        res_ship = False
        if ship:
            ship_list = self.get_address_list(ship)
            bill_list = self.get_address_list(bill)
            if not self.get_ship_to_bill(ship_list, bill_list):  # bill == ship aynı olma ihtimali yüksek
                res_ship = self.get_shipping(ship_list, item, lang, res_bill)
            else:
                # bill == ship aynı sadece ship'da vat var. bizde bunu bill ekliyoruz.
                if not res_bill.vat and ship_list.get('vat', ''):
                    res_bill.with_context(no_vat_validation=True).write({
                        'vat': ship_list.get('vat', ''),
                    })
                res_ship = False
        else:
            res_ship = False

        if res_contact:
            res_bill = res_contact
        if not res_contact:
            res_contact = res_bill
        if not res_ship:
            res_ship = res_bill

        return res_contact, res_bill, res_ship

    def get_address_list(self, list):
        _logger.info("get_address_list")
        street = self.get_street(list.get('street', []))
        return {
            'company': (list.get('company') or '').strip(),
            'name': f"{list.get('firstname') or ''} {list.get('lastname') or ''}".strip(),
            'country_id': self.get_country(list.get('country_id')),
            'city': (list.get('city') or '').strip(),
            'zip': (list.get('postcode') or '').strip(),
            'phone': (list.get('telephone') or '').strip(),
            'email': (list.get('email') or '').strip(),
            'vat': (list.get('vat_id') or '').strip(), # boşluklar geliyor. odoo bu boşlukları kaldırıyor.
            'street': (street.get('street') or '').strip(),
            'street2': (street.get('street2') or '').strip(),
        }

    @staticmethod
    def get_street(streets):
        street1 = street2 = ''
        if len(streets):
            street1 = streets[0]
            if len(streets) == 2:
                street2 = streets[1]
            elif len(streets) == 3:
                street2 = f"{streets[1]}, {streets[2]}"
            elif len(streets) == 4:
                street2 = f"{streets[1]}, {streets[2]}, {streets[3]}"
        return {
            'street': street1,
            'street2': street2
        }

    def get_country(self, country_name_or_code):
        country = self.env['res.country'].search(['|', ('code', '=ilike', country_name_or_code),
                                                  ('name', '=ilike', country_name_or_code)], limit=1)
        return country.id or False

    def get_ship_to_bill(self, ship, bill):
        return all(bill.get(key) == ship.get(key) for key in bill if key not in ['vat'])

    # Billing
    def get_billing(self, bill_list, item):
        _logger.info("get_billing")
        domain = []
        values = {}
        if bill_list.get('company', ''):
            bill_list['name'] = bill_list['company']
            bill_list.pop('company', None)
            for key, value in bill_list.items():
                if value and key in ['phone']:
                    domain.append((key, 'ilike', value))
                elif value and key not in ['vat']:
                    domain.append((key, '=', value))
            domain.append(('company_type', '=', 'company'))
            values = {'company_type': 'company', 'magento': True, 'magento_id': item.get('customer_id', False), 'active': True}
        else:
            bill_list.pop('company', None)
            for key, value in bill_list.items():
                if value:
                    domain.append((key, '=', value))
            domain.append(('company_type', '=', 'person'))
            domain.append(('type', '=', 'invoice'))
            values = {'company_type': 'person', 'type': 'invoice', 'magento': True, 'magento_id': item.get('customer_id', False), 'active': True}

        bill_list.update(values)
        partner = self.env['res.partner'].search(domain, limit=1)
        # gerek yok vat müşteri değiştirsede datev de kullanılmıyor.
        # if partner.vat and partner.vat.replace(" ", "") != bill_list.get('vat','').replace(" ", "") :
        #     partner = False
        if not partner:
            #raise models.ValidationError(f" Billing  {domain} ================== {bill_list}")
            partner = self.env['res.partner'].with_context(no_vat_validation=True).create(bill_list)
        return partner, bill_list

    # Contact
    def get_billing_contact(self, bill, lang, res_bill):
        _logger.info("get_billing_contact")
        res_contact = False
        contact_name = f"{bill.get('firstname') or ''} {bill.get('lastname') or ''}".strip()
        values_contact = {
            'type': 'contact', 'name': contact_name, 'magento': True, 'active': True,
            'parent_id': res_bill.id, 'magento_id': res_bill.magento_id or False,
            'lang': lang
        }
        if bill.get('company', ''):
            contact = self.env['res.partner'].search([
                ('name', '=', contact_name),
                ('type', '=', 'contact'), ('parent_id', '=', res_bill.id)], limit=1)
            if contact:
                return contact
            else:
                #raise models.ValidationError(f"contact ==========")
                res_contact = self.env['res.partner'].with_context(no_vat_validation=True).create(values_contact)

        return res_contact

    # Shipping
    def get_shipping(self, ship_list, item, lang, res_bill):
        _logger.info("get_shipping")
        domain = []
        if res_bill.name != ship_list['company'] and ship_list['company']:
            ship_list['name'] = f"{ship_list['company']}, {ship_list['name']}"
        ship_list.pop('company', None)
        for key, value in ship_list.items():
            if value and key not in ['vat']:
                domain.append((key, '=', value))
        domain.append(('type', '=', 'delivery'))
        domain.append(('parent_id', '=', res_bill.id))
        values = {'type': 'delivery', 'parent_id': res_bill.id, 'lang': lang,
                  'magento': True, 'magento_id': item.get('customer_id', False), 'active': True}

        ship_list.update(values)
        delivery = self.env['res.partner'].search(domain, limit=1)
        if not delivery:
            #raise models.ValidationError(f" Shipping  {domain} ================== {ship_list}")
            # no_vat_validation= True olması Vat kontrolü yapmıyor.
            delivery = self.env['res.partner'].with_context(no_vat_validation=True).create(ship_list)
        return delivery





    def fetch_customers(self):
        """Fetch products"""
        PartnerObj = self.env['res.partner']
        cr = self._cr
        url = '/rest/V1/customers/search?searchCriteria=0'
        type = 'GET'
        customer_list = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
        try:
            items = customer_list['items']

            cr.execute("select magento_id from res_partner "
                       "where magento_id is not null")
            partners = cr.fetchall()
            partner_ids = [i[0] for i in partners] if partners else []

            _logger.warning(f"partner_ids: {partner_ids}")

            # need to fetch the complete required fields list
            # and their values

            cr.execute("select id from ir_model "
                       "where model='res.partner'")
            partner_model = cr.fetchone()

            if not partner_model:
                return
            cr.execute("select name from ir_model_fields "
                       "where model_id=%s and required=True "
                       " and store=True",
                       (partner_model[0],))
            res = cr.fetchall()
            fields_list = [i[0] for i in res if res] or []
            partner_vals = self.env['res.partner'].default_get(fields_list)

            _logger.warning(f"partner_vals: {partner_vals}")

            for i in items:
                if str(i['id']) not in partner_ids:
                    _logger.warning(f"{i}")

                    # customer_id = self.find_customer_id(
                    #     i,
                    #     partner_ids,
                    #     partner_vals,
                    #     main=True
                    # )
                    #
                    # if customer_id:
                    #     _logger.info("Customer is created with id %s", customer_id)
                    # else:
                    #     _logger.info("Unable to create order")

            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)
