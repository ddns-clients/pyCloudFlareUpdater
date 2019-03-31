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


def get_machine_public_ip():
    import urllib.request

    return urllib.request.urlopen('https://ident.me').read().decode('utf8')


class CloudFlare(object):
    def __init__(self, domain, name, key, mail):
        self.__domain = domain
        self.__name = name
        self.__headers = {"X-Auth-Email": mail,
                          "X-Auth-Key": key,
                          "Content-Type": "application/json"}
        self.__zone = self._get_zone()
        self.__id = self._get_identifier()

    def _get_zone(self):
        try:
            import ujson as json
        except ImportError:
            import json
        from urllib.request import Request, urlopen

        from ..values import cloudflare_base_url

        url_extra_attrs = "zones?name={0}&status=active&page=1&per_page=1&match=all".format(self.__name)
        request = Request(cloudflare_base_url.format(url_extra_attrs), headers=self.__headers)
        result = json.loads(urlopen(request).read().decode("utf8"))
        if not result["success"]:
            raise ValueError("CloudFlare returned error code with the request data - more info: " + result["errors"][0])

        return result["result"][0]["id"]

    def _get_identifier(self):
        try:
            import ujson as json
        except ImportError:
            import json
        from urllib.request import Request, urlopen

        from ..values import cloudflare_base_url

        url_extra_attrs = "zones/{0}/dns_records?type=A&name={1}&page=1&per_page=1".format(self.__zone, self.__name)
        request = Request(cloudflare_base_url.format(url_extra_attrs), headers=self.__headers)
        result = json.loads(urlopen(request).read().decode("utf8"))
        if not result["success"]:
            raise ValueError("CloudFlare returned error code with the request data - more info: " + result["errors"][0])

        return result["result"][0]["id"]

    def get_cloudflare_latest_ip(self):
        try:
            import ujson as json
        except ImportError:
            import json
        from urllib.request import Request, urlopen
        from ..values import cloudflare_base_url

        url_extra_attrs = "zones/{0}/dns_records/{1}".format(self.__zone, self.__id)
        request = Request(cloudflare_base_url.format(url_extra_attrs), headers=self.__headers)
        result = json.loads(urlopen(request).read().decode("utf8"))

        return result["result"]["content"]

    def set_cloudflare_ip(self, ip):
        try:
            from ujson import dumps
        except ImportError:
            from json import dumps
        from urllib.request import Request, urlopen
        from ..values import cloudflare_base_url

        data = dumps({"type": "A", "name": self.__name, "content": ip, "ttl": 600, "proxied": False})
        url_extra_attrs = "zones/{0}/dns_records/{1}".format(self.__zone, self.__id)
        request = Request(url=cloudflare_base_url.format(url_extra_attrs),
                          data=data.encode("utf-8"),
                          headers=self.__headers,
                          method="PUT")
        return urlopen(request).getcode()
