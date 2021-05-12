#                             pyCloudflareUpdater
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
from ..utils import CLOUDFLARE_BASE_URL


async def get_machine_public_ip():
    return requests.get('https://ident.me/').text


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

    async def _do_request(self,
                          path: str,
                          method: str = 'GET',
                          data=None) -> json:
        tmp_headers = self._construct_headers()
        if self.session.headers != tmp_headers:
            self.session.headers.update(tmp_headers)
        url = CLOUDFLARE_BASE_URL.format(path)
        req = self.session.request(method, url, data=data)
        req.encoding = 'utf-8'
        res = json.loads(req.text)

        if req.status_code >= 304 or not res['success']:
            error_json = res['errors'][0]
            error_msg = [f"({error_json['code']}) {error_json['message']}"]
            for error in error_json['error_chain']:
                error_msg.append(f"\t- ({error['code']}) {error['message']}")
            raise requests.HTTPError('\n'.join(error_msg),
                                     request=url,
                                     response=error_json)
        return res['result']

    @property
    async def zone(self) -> str:
        path = f"zones?name={self.preferences.name}" \
               f"&status=active&page=1&per_page=1&match=all"
        r = await self._do_request(path)
        return r[0]['id']

    @property
    async def identifier(self) -> str:
        path = f"zones/{self.zone}/dns_records?type=A" \
               f"&name={self.preferences.name}&page=1&per_page=1"
        r = await self._do_request(path)
        return r[0]['id']

    @property
    async def ip(self) -> str:
        path = f"zones/{self.zone}/dns_records/{self.identifier}"
        r = await self._do_request(path)
        return r['content']

    @ip.setter
    async def ip(self, new_ip: str):
        data = {
            'type': 'A',
            'name': self.preferences.name,
            'content': new_ip,
            'ttl': 600,
            'proxied': self.preferences.use_proxy
        }
        path = f"zones/{self.zone}/dns_records/{self.identifier}"
        await self._do_request(path, method='POST', data=data)
