# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LoyaltyController(http.Controller):
    @http.route(['/payment/loyalty/return', '/payment/loyalty/cancel', '/payment/loyalty/error'], type='http', auth='public', csrf=False)
    def loyalty_return(self, **post):
        _logger.info(
            'loyalty: entering form_feedback with post data %s', pprint.pformat(post))
        headers = {
            'authorization': '9321ee29-bff1-4d33-b547-a9bcbe836d6e',
            }
        if post:
            request.env['payment.transaction'].sudo().form_feedback(post, 'loyalty',headers=headers)
        return werkzeug.utils.redirect('/payment/process')
