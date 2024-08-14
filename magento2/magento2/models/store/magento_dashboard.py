import calendar
from odoo import models, api
from dateutil.relativedelta import relativedelta
from datetime import date


class MagentoDashboard(models.Model):
    _name = 'magento.dashboard'
    _description = 'Magento Dashboard'

    def this_year(self):
        self._cr.execute('''SELECT sum(amount_total) FROM sale_order WHERE
                            sale_order.magento = True
                            AND 
                            sale_order.state != 'cancel'
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')

        record = self._cr.dictfetchall()
        self._cr.execute('''SELECT count(id) FROM sale_order WHERE
                            sale_order.magento = True
                            AND 
                            sale_order.state != 'cancel'
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        self._cr.execute('''SELECT sum(amount_total) - sum(amount_residual)
                            as invoiced 
                            FROM account_move WHERE
                            account_move.magento = True
                            AND 
                            account_move.state != 'cancel'
                            AND
                            account_move.move_type != 'out_refund'
                            AND
                            Extract(Year FROM account_move.invoice_date) = 
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        record.extend([{'symbol': self.env.company.currency_id.symbol}])

        return record

    def this_quarter(self):
        self._cr.execute('''SELECT sum(amount_total) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(QUARTER FROM sale_order.date_order) = 
                            Extract(QUARTER FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')

        record = self._cr.dictfetchall()
        self._cr.execute('''SELECT count(id) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(QUARTER FROM sale_order.date_order) = 
                            Extract(QUARTER FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) =
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        self._cr.execute('''SELECT sum(amount_total) - sum(amount_residual)
                            as invoiced
                            FROM account_move WHERE
                            account_move.magento = True
                            AND 
                            account_move.state != 'cancel'
                            AND
                            account_move.move_type != 'out_refund'
                            AND
                            Extract(QUARTER FROM account_move.invoice_date) = 
                            Extract(QUARTER FROM DATE(NOW()))
                            AND
                            Extract(Year FROM account_move.invoice_date) =
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        record.extend([{'symbol': self.env.company.currency_id.symbol}])
        # shipment_shipment

        return record

    def this_month(self):
        self._cr.execute('''SELECT sum(amount_total) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')

        record = self._cr.dictfetchall()

        self._cr.execute('''SELECT count(id) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())


        self._cr.execute('''SELECT sum(amount_total) - sum(amount_residual)
                            as invoiced 
                            FROM account_move WHERE
                            account_move.magento = True
                            AND 
                            account_move.state != 'cancel'
                            AND
                            account_move.move_type != 'out_refund'
                            AND
                            Extract(MONTH FROM account_move.invoice_date) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Year FROM account_move.invoice_date) = 
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        record.extend([{'symbol': self.env.company.currency_id.symbol}])
        return record

    def this_week(self):
        self._cr.execute('''SELECT sum(amount_total) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Week FROM sale_order.date_order) = 
                            Extract(Week FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')

        record = self._cr.dictfetchall()
        self._cr.execute('''SELECT count(id) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Week FROM sale_order.date_order) = 
                            Extract(Week FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) =
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        self._cr.execute('''SELECT sum(amount_total) - sum(amount_residual)
                            as invoiced
                            FROM account_move WHERE
                            account_move.magento = True
                            AND
                            account_move.state != 'cancel'
                            AND
                            Extract(MONTH FROM account_move.invoice_date) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Week FROM account_move.invoice_date) = 
                            Extract(Week FROM DATE(NOW()))
                            AND
                            Extract(Year FROM account_move.invoice_date) =
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        record.extend([{'symbol': self.env.company.currency_id.symbol}])

        return record

    def sales_today(self):
        self._cr.execute('''SELECT count(id) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(DAY FROM sale_order.date_order) =
                            Extract(DAY FROM DATE(NOW()))
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) =
                            Extract(Year FROM DATE(NOW()));''')
        record = self._cr.dictfetchall()
        self._cr.execute('''SELECT sum(amount_total) FROM sale_order WHERE
                            sale_order.magento = True
                            AND
                            sale_order.state != 'cancel'
                            AND
                            Extract(DAY FROM sale_order.date_order) =
                            Extract(DAY FROM DATE(NOW()))
                            AND
                            Extract(MONTH FROM sale_order.date_order) =
                            Extract(MONTH FROM DATE(NOW()))
                            AND
                            Extract(Year FROM sale_order.date_order) =
                            Extract(Year FROM DATE(NOW()));''')
        record.extend(self._cr.dictfetchall())

        currency = self.env.user.company_id.currency_id.symbol
        if record[1]['sum'] is None:
            record[1]['sum'] = 0
        res = {
            'count_today': [record[0]['count']],
            'amt_today': [record[1]['sum']],
            'currency': [currency],
        }
        return res

    def sales_7(self):
        self._cr.execute('''select count(*),
                            Extract(Day From sale_order.date_order)
                            as date from sale_order
                            WHERE magento = True
                            AND state != 'cancel'
                            AND date_order > current_date - 7
                            GROUP BY Extract
                            (Day From sale_order.date_order);''')
        record = self._cr.dictfetchall()
        days_7 = []
        days_name = []
        count_7 = []
        for i in range(6, -1, -1):
            days_7.append((date.today() - relativedelta(days=i)).
                          strftime("%d"))
            days_name.append((date.today() - relativedelta(days=i)).
                             strftime('%A'))
            count_7.append(0)
        for rec in record:
            day = ''
            days = str(int((rec['date'])))
            if len(days) == 1:
                day = '0' + days
            else:
                day = days
            if day in days_7:
                count_7[days_7.index(day)] = rec['count']
        self._cr.execute('''select sum(amount_total)
                            from sale_order
                            WHERE magento = True
                            AND state != 'cancel'
                            AND date_order > current_date - 7
                            ''')
        total_amt = self._cr.dictfetchall()
        currency = self.env.user.company_id.currency_id.symbol
        res = {
            'days': days_7,
            'days_name': days_name,
            'count': count_7,
            'amt_7': total_amt[0]['sum'],
            'currency': currency,
        }
        return res

    def annual_growth(self):
        currency = self.env.user.company_id.currency_id.symbol
        months = list(calendar.month_name)
        months.pop(0)
        self._cr.execute('''SELECT COUNT(*) as count,
                            Extract(Month From sale_order.date_order)
                            as month FROM sale_order
                            WHERE magento = True
                            AND state != 'cancel'
                            AND
                            Extract(Year FROM sale_order.date_order)
                            =
                            Extract(Year FROM DATE(NOW()))
                            GROUP BY
                            Extract(Month From sale_order.date_order)''')
        record = self._cr.dictfetchall()
        self._cr.execute('''SELECT sum(amount_total) as total_amt
                            FROM sale_order WHERE
                            sale_order.magento = True
                            AND 
                            sale_order.state != 'cancel'
                            AND
                            Extract(Year FROM sale_order.date_order) = 
                            Extract(Year FROM DATE(NOW()));''')
        total = self._cr.dictfetchall()
        count = [0] * 12
        for rec in record:
            count[int(rec['month'])-1] = rec['count']
        res = {
            'months': months,
            'orders': count,
            'total_year': total[0]['total_amt'],
            'currency': currency,
        }
        return res