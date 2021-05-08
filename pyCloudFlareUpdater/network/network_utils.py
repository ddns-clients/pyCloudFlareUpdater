#                             pyCloudFlareUpdater
#                  Copyright (C) 2019 - Javinator9889
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#                   (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#               GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
try:
    import ujson as json
except ImportError:
    import json
import requests
from cachecontrol import CacheControlAdapter
from ..preferences import Preferences
from ..values import CLOUDFLARE_BASE_URL


def get_machine_public_ip():
    return requests.get('https://ident.me').text


class Cloudflare:
    def __init__(self, preferences: Preferences):
        self.preferences = preferences
        self.session = requests.Session()
        self.session.mount('https://', CacheControlAdapter())
        self.session.headers.update(self._construct_headers())

    def _construct_headers(self) -> dict:
        return {
            'X-Auth-Email': self.preferences.mail,
            'X-Auth-Key': self.preferences.key,
            'Content-Type': 'application/json'
        }

    def _do_request(self, path: str, method: str = 'GET', data=None) -> json:
        tmp_headers = self._construct_headers()
        if self.session.headers != tmp_headers:
            self.session.headers.update(tmp_headers)
        req = self.session.request(method,
                                   CLOUDFLARE_BASE_URL.format(path),
                                   data=data)
        req.encoding = 'utf-8'
        res = json.loads(req.text)
        if req.status_code >= 304 or not res['success']:
            raise requests.HTTPError("Cloudflare GET failure - error: %s"
                                     % res['errors'][0])
        return res['result']

    @property
    def zone(self) -> str:
        path = "zones?name={0}&status=active&page=1&per_page=1&match=all" \
            .format(self.preferences.A)
        return self._do_request(path)[0]['id']

    @property
    def identifier(self) -> str:
        path = "zones/{0}/dns_records?type=A&name={1}&page=1&per_page=1" \
            .format(self.zone, self.preferences.A)
        return self._do_request(path)[0]['id']

    @property
    def ip(self) -> str:
        path = "zones/{0}/dns_records/{1}".format(self.zone,
                                                  self.identifier)
        return self._do_request(path)['content']

    @ip.setter
    def ip(self, new_ip: str):
        data = {
            'type': 'A',
            'name': self.preferences.A,
            'content': new_ip,
            'ttl': 600,
            'proxied': self.preferences.use_proxy
        }
        path = "zones/{0}/dns_records/{1}".format(self.zone,
                                                  self.identifier)
        self._do_request(path, method='POST', data=data)
