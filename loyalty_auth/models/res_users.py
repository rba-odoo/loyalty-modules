from odoo import api, fields, models
# from urllib2 import urlopen
import requests
import logging
import base64

_logger = logging.getLogger(__name__)

FULL_VALIDATION = []

class ResUsers(models.Model):
	_inherit = 'res.users'

	user_points = fields.Integer(string="User Points", related="partner_id.user_points")

	@api.model
	def _get_backend_user_values(self, user):
		HEADERS = {
			'authorization': '9321ee29-bff1-4d33-b547-a9bcbe836d6e',
		}
		member_url = "http://3.231.100.180/member/Member"
		member_params = {'programCode': "raktim.0526", 'tierName': "Platinum", 'memberNumber': user}
		try:
			response = requests.get(member_url, params=member_params, headers=HEADERS)
			member_response = response.json()
		except Exception as e:
			raise e
		_logger.info(member_response)
		return member_response['response']

	@api.model
	def _auth_oauth_signin(self, provider, validation, params):
		res = super(ResUsers, self)._auth_oauth_signin(provider, validation, params)
		partner = self.env['res.partner'].search([('email', '=', res)])
		all_fields = self._get_backend_user_values(res.split('@')[0])
		_logger.info(all_fields)
		update_fields = {
			'user_points': all_fields['balance']
		}
		partner.write(update_fields)
		return res
