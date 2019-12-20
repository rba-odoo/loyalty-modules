# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale  # Import the class

_logger = logging.getLogger(__name__)


class LoyaltyController(http.Controller):

    @http.route(['/payment/loyalty/create_charge'], type='http', auth='public', csrf=False)
    def loyalty_return(self, **post):
        response = request.env['payment.transaction'].sudo()._create_loyalty_charge(post)
        if response:
            _logger.info(
                'loyalty: entering form_feedback with post data %s', pprint.pformat(response.get('response')))
            if response.get('response'):
                request.env['payment.transaction'].sudo().form_feedback(response.get('response'), 'loyalty')
            else:
                request.env['payment.transaction'].sudo().form_feedback(response, 'loyalty')
        return werkzeug.utils.redirect('/payment/process')


class CustomWebsiteSale(WebsiteSale):  # Inherit in your custom class

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="user", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super(CustomWebsiteSale, self).shop(page=0, category=None, search='', ppg=False, **post)
        return res
