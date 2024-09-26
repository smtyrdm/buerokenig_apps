from odoo import api, fields, models
class IrLogging(models.Model):
    _inherit = "ir.logging"

    def magento_ir_logging(self, data, email=False):
        # Bağımsız bir cr (cursor) ile kayıt oluşturma
        with self.pool.cursor() as new_cr:
            self.with_env(self.env(cr=new_cr)).create({
                'name': 'magento',
                'type': 'server',
                'dbname': self.env.cr.dbname,
                'level': 'ERROR',
                'message': data.get('message',''),
                'path': data.get('path',''),
                'func': data.get('func',''),
                'line': data.get('line',''),
            })
            #self.env.cr.commit()
            new_cr.commit()
        if email:
            mail_values = {
                'subject': "Magento Hata Bilgilendirme",
                'body_html': f"{data}  | ir_logging_id:{self.id} | Not:Silmediğin sürece sipariş gelmez..",
                'email_to': "enginulger06@gmail.com",
                'auto_delete': True,
                'email_from': self.env.company.email,  # Gönderenin e-postası
            }
            self.env['mail.mail'].create(mail_values).send()