
import logging
from odoo import models, fields, exceptions, _, api

logger = logging.getLogger(__name__)

class MagentoIncoterm(models.Model):
    _inherit = 'magento.account.incoterm'

    def find_magento_incoterm(self,i, name):
        # Incoterm

        ship_country = i.get("extension_attributes", {}).get("shipping_assignments", [{}])[0].get("shipping", {}).get("address", {}).get('country_id','')
        bill_country = i.get("billing_address", {}).get('country_id','')
        country = ship_country or bill_country # bazen magento hatasından dolayı ship gelmeyebilir.
        inco = self.env['magento.account.incoterm'].search([('code','=',country)], limit=1)

        if name == 'incoterm':
            if not inco or inco and not inco.incoterm_id:
                raise models.ValidationError(f"Account/Magento Incoterm: code: {country} incoterm not!")
            incoterm = inco.incoterm_id
            return incoterm

        elif name == 'shipping':
            if not inco or inco and not inco.product_ship_id:
                raise models.ValidationError(f"Account/Magento Incoterm: code: {country} Shipping Product not!")
            ship = inco.product_ship_id
            return ship

        elif name == 'discount':
            if not inco or inco and not inco.product_disc_id:
                raise models.ValidationError(f"Account/Magento Incoterm: code: {country} Discount Product not!")
            disc = inco.product_disc_id
            return disc
        else:
            raise models.ValidationError("Gelen name yok. (find_magento_incoterm)")