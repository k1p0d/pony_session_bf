import socket
import urllib2
import urllib
import copy
from urllib import urlencode

HTTP_CLIENT_TIMEOUT = 4
# TODO: take care of urllib2.HTTPError exceptions in particularly and handle the rest the same way
class ControlPanelNegotiator(object):
	def __init__(self, url, auth_cookie_hash = False):
		self.client = urllib2.urlopen
		req = urllib2.Request(url)
		self.url = url
		if auth_cookie_hash:
			self.auth_cookie_hash = auth_cookie_hash

		self._cp_map  = {'ftp' : ['download_ftp',
								 'download_ssh',
								 'filter_download'], 
						'http': ['download_http',
								 'filter_download'],
						'other': ['download_email', 
								  'download_cert',
								  'download_rdp']
						}

		self._data_sections = ['http', 'ftp']
		self._filters = ['filter_date_from', 'filter_date_to']

	def _get_request(self):
		req = urllib2.Request(self.url)
		req.add_header('Cookie', 'auth_cookie=' + self.auth_cookie_hash)
		req.add_header('User-Agent','Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20100101 Firefox/21.0')		
		return req

	def _page(self, action, routine, **kwargs_params):
		request = self._get_request()
		if action not in self._cp_map.keys():
			raise ControlPanelError,'The action "%s" is unknown/unsupported'
		elif routine not in self._cp_map[action]:
			raise ControlPanelError, 'The routine "%s" is unknown/unsupported'

		data = {"action" : action, "routine" : routine}
		data.update(kwargs_params)
		request.add_data(urllib.urlencode(data))
		try:
			response = self.client(request, timeout = HTTP_CLIENT_TIMEOUT)
			# TODO: if needed refactor this check into pages requests that belongs to data retreival
			if not response.headers.get('Content-Disposition'):
	 			raise ControlPanelDataRetreivalError,'Received an unexpected response from server'
			return response
		except Exception as e:
			raise ControlPanelError, 'Unable to fetch url "%s" reason %s' % (request.get_full_url, e.message)


	def download_ftp(self, **filters):
		if filters:
			return self._page('ftp', 'filter_download', **filters)
		else:
			return self._page('ftp', 'download_ftp')


	def download_http(self, **filters):
		if filters:
			return self._page('http', 'filter_download', **filters)
		else:
			return self._page('http', 'download_http')

	def download_ssh(self):
		return self._page('ftp', 'download_ssh')


	def download_email(self):
		return self._page('other', 'download_email')

	def download_rdp(self):
		return self._page('other', 'download_rdp')

	def download_cert(self):
		return self._page('other', 'download_cert')




	""" This method is deprecated"""
	def retreive_data(self, section, **filters):
		if section not in self._data_sections:
			raise ValueError, "Unknown section used. should be one of the following " + ",".join(self._data_sections) 
		unknown_filters = [v for v in filters.keys() if v not in self._filters]
		if unknown_filters:
			raise ValueError, "Unknown filters " + ", ".join(unknown_filters)

		request = self._get_request()
		data = {"routine" : 'filter_download', "action" : section }
		data.update(filters)
		request.add_data(urllib.urlencode(data))
	 	try:
	 		response = self.client(request, timeout = HTTP_CLIENT_TIMEOUT)
	 	except urllib2.HTTPError, response:
	 		pass
	 	if not response.headers.get('Content-Disposition'):
	 		raise ControlPanelDataRetreivalError,'Received an unexpected response from server'
	 	response_data = response.read()
	 	return (len(response_data), response_data)




	def is_session_valid(self, request = False):
		""" check if the given auth_cookie is still active and enable us to enter the panel """
		try:
			response = self.client(request or self._get_request(), timeout = HTTP_CLIENT_TIMEOUT).read()
		except:
			return False # TODO: better handling required here
		if response.find('<form name="login_frm"') >= 0:
			return False
		elif response.find('table_logins') >= 0:
			return True
		else:
			raise ControlPanelError('Received unknown response from the server: %s' % response)

	@staticmethod
	def is_admin_cp(url):

		client = urllib2.urlopen
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20100101 Firefox/21.0')
		try:
			response = client(req, timeout = HTTP_CLIENT_TIMEOUT).read()
		except:
			return False
		if response.find('<form name="login_frm"') >= 0:
			return True

class ControlPanelError(Exception):
	pass

class ControlPanelDataRetreivalError(Exception):
	pass