# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib

from werkzeug import urls
import requests

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerLoyalty(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('loyalty', 'Loyalty')])
    loyalty_merchant_key = fields.Char(string='Merchant Key', required_if_provider='loyalty', groups='base.group_user')

    def _get_loyalty_urls(self):
        return 'http://3.231.100.180/merchant/useFunds'

    def loyalty_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.get_base_url()
        user = self.env.user
        if values['amount'] > user.user_points:
            raise ValidationError(_('Insufficent point balance, Current point balance is %s') % (user.user_points))

        _logger.info(user)
        values.update({
            "programCode": "raktim.0526",
            "tierName": "Platinum",
            "memberNumber": user.email.split('@')[0],
            "merchantCode": "merchant1",
            "txnid": values['reference'],
            "amount_input": values['amount'],
            })
        return values

    def loyalty_get_form_action_url(self):
        self.ensure_one()
        base_url = self.get_base_url()
        prod_url = '/payment/loyalty/create_charge'
        valid_url = urls.url_join(base_url, prod_url)
        return valid_url


class PaymentTransactionLoyalty(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _loyalty_form_get_tx_from_data(self, data):
        reference = data.get('txnid')
        if not reference:
            raise ValidationError(_('loyalty: received data with missing reference (%s)') % (reference))

        transaction = self.search([('reference', '=', reference)])

        if not transaction:
            error_msg = (_('loyalty: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('loyalty: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)

        return transaction

    def _loyalty_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        #check what is buyed
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(
                ('Amount', data.get('amount'), '%.2f' % self.amount))

        return invalid_parameters

    def _loyalty_form_validate(self, data):
        status = data.get('status')
        result = self.write({
            'acquirer_reference': data.get('txId'),
            'date': fields.Datetime.now(),
        })
        if status == 'success':
            self._set_transaction_done()
        else:
            self._set_transaction_cancel()
        return True

    @api.model
    def _create_loyalty_charge(self, data):
        HEADERS = {
            'authorization': '9321ee29-bff1-4d33-b547-a9bcbe836d6e',
            }
        payment_acquirer = self.env['payment.acquirer'].search([('provider', '=', 'loyalty')], limit=1)
        payment_url = payment_acquirer._get_loyalty_urls()
        user = self.env.user.email
        _logger.info(user)
        charge_params =  dict(  programCode="raktim.0526",
                                tierName="Platinum",
                                memberNumber=user.split('@')[0],
                                merchantCode = "merchant1",
                                amount_input=data.get('amount'),
                                )
        try:
            response = requests.post(payment_url,data=charge_params,headers=HEADERS)
            payment_response = response.json()
        except Exception as e:
            raise e
        print('response',payment_response,response.status_code)
        payment_reference = payment_response.get('response',{}).get('txId', False) if type(payment_response.get('response')) == dict else False
        if response.status_code == 200 and payment_reference:
            reference = data.get('txnid', False)
            self.env.user.partner_id.write({'user_points': self.env.user.partner_id.user_points - round(float(data.get('amount')))})
            payment_response.get('response', {}).update({'status': 'success', 'txnid': reference, 'amount': data.get('amount', 0)})
            return payment_response
        elif response.status_code == 200 and not payment_reference:
            return data
        else:
            return data