# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerLoyalty(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('loyalty', 'Loyalty')])
    loyalty_merchant_key = fields.Char(string='Merchant Key', required_if_provider='loyalty', groups='base.group_user')

    def _get_loyalty_urls(self, environment):
        if environment == 'prod':
            return {'loyalty_form_url': 'http://3.231.100.180/merchant/useFunds'}
        else:
            return {'loyalty_form_url': 'http://3.231.100.180/merchant/useFunds'}

    def loyalty_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.get_base_url()
        loyalty_values = dict(values,
                                programCode="raktim.0526",
                                tierName="Platinum",
                                memberNumber="m1",
                                merchantCode = "merchant1",
                                txnid=values['reference'],
                                amount_input=values['amount'],
                                surl='http://3.231.100.180/merchant/undoUseFunds',
                                )
        return loyalty_values

    def loyalty_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_loyalty_urls(environment)['loyalty_form_url']


class PaymentTransactionLoyalty(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _loyalty_form_get_tx_from_data(self, data):
        """ Given a data dict coming from payumoney, verify it and find the related
        transaction record. """
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
            'acquirer_reference': data.get('transactionId'),
            'date': fields.Datetime.now(),
        })
        if status == 'success':
            self._set_transaction_done()
        elif status != 'pending':
            self._set_transaction_cancel()
        else:
            self._set_transaction_pending()
        return result

    def _create_loyalty_charge(self, acquirer_ref=None, tokenid=None, email=None):
        api_url_charge = '%s' % (self.acquirer_id.loyalty_get_form_action_url())
        charge_params =  dict(values,
                                programCode="raktim.0526",
                                tierName="Platinum",
                                memberNumber="m1",
                                merchantCode = "merchant1",
                                txnid=values['reference'],
                                amount_input=values['amount'],
                                )
        HEADERS = {
            'Authorization': '9321ee29-bff1-4d33-b547-a9bcbe836d6e',
            }
        r = requests.post(api_url_charge,
                          data=charge_params,
                          headers=HEADERS)
        return r.json()
