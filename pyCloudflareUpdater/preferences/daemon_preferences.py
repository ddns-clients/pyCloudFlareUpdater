#                             pyCloudflareUpdater
#                  Copyright (C) 2021 - Javinator9889
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
from .. import PRODUCTION_FILE_LOG_LEVEL, VALID_LOGGING_LEVELS
from configparser import ConfigParser
from typing import Union
from pathlib import Path
import warnings
import logging
import os


class Preferences:
    __instance__ = None

    def __new__(cls, *args, **kwargs):
        if Preferences.__instance__ is None:
            instance = object.__new__(cls)
            instance.__must_init = True
            Preferences.__instance__ = instance
        return Preferences.__instance__

    def __init__(self,
                 domain: str = None,
                 name: str = None,
                 update_time: int = None,
                 key: str = None,
                 mail: str = None,
                 use_proxy: bool = False,
                 pid_file: str = None,
                 log_file: str = None,
                 log_level: int = PRODUCTION_FILE_LOG_LEVEL):
        if self.__must_init:
            self.config = ConfigParser()
            self.file = "%s/.config/cloudflare-ddns.ini" % Path.home()
            self.config.read(self.file)
            home = Path.home()
            uid = os.geteuid()
            log_file = \
                log_file or "/var/log/cloudflare-ddns.log" if uid == 0 \
                    else "%s/log/cloudflare-ddns.log" % home
            pid_file = \
                pid_file or "/var/run/cloudflare-ddns.pid" if uid == 0 \
                    else "%s/.cache/cloudflare-ddns.pid" % home

            log_file_dir = os.path.dirname(log_file)
            if not os.path.exists(log_file_dir):
                os.makedirs(log_file_dir, mode=0o750, exist_ok=True)

            pid_file_dir = os.path.dirname(pid_file)
            if not os.path.exists(pid_file_dir):
                os.makedirs(pid_file_dir, mode=0o700, exist_ok=True)
            if 'Logging' not in self.config:
                self.config['Logging'] = {}
            if 'Cloudflare' not in self.config:
                self.config['Cloudflare'] = {}
            if 'Service' not in self.config:
                self.config['Service'] = {}

            cloudflare = self.config['Cloudflare']
            log = self.config['Logging']
            service = self.config['Service']

            self.domain = cloudflare.get('domain', domain)
            self.name = cloudflare.get('name', name)
            self.frequency = int(
                cloudflare.get('frequency-minutes', update_time))
            self.key = cloudflare.get('api-key', key)
            self.mail = cloudflare.get('mail', mail)
            self.use_proxy = bool(cloudflare.get('use-proxy', str(use_proxy)))

            self.logging_file = log.get('file', log_file)
            self.logging_level = \
                log.get('level', logging.getLevelName(log_level))

            self.pid_file = service.get('pid-file', pid_file)

            with open(self.file, 'w') as configfile:
                self.config.write(configfile)

    @property
    def domain(self) -> str:
        return self.config['Cloudflare']['domain']

    @domain.setter
    def domain(self, new_domain: str):
        if new_domain is None:
            raise ValueError("Domain must be provided!")
        self.config['Cloudflare']['domain'] = new_domain

    @property
    def name(self) -> str:
        return self.config['Cloudflare']['name']

    @name.setter
    def name(self, new_A: str):
        if new_A is None:
            raise ValueError("'A' record must be provided!")
        self.config['Cloudflare']['name'] = new_A

    @property
    def frequency(self) -> int:
        return int(self.config['Cloudflare']['frequency-minutes'])

    @frequency.setter
    def frequency(self, new_freq: int):
        if new_freq is None:
            raise ValueError("Update frequency must be provided")
        self.config['Cloudflare']['frequency-minutes'] = str(new_freq)

    @property
    def key(self) -> str:
        return self.config['Cloudflare']['api-key']

    @key.setter
    def key(self, new_key: str):
        if new_key is None:
            raise ValueError("API key must be provided!")
        self.config['Cloudflare']['api-key'] = new_key

    @property
    def mail(self) -> str:
        return self.config['Cloudflare']['mail']

    @mail.setter
    def mail(self, new_mail: str):
        if new_mail is None:
            raise ValueError("Mail must be provided!")
        self.config['Cloudflare']['mail'] = new_mail

    @property
    def use_proxy(self) -> bool:
        return bool(self.config['Cloudflare']['use-proxy'])

    @use_proxy.setter
    def use_proxy(self, use: bool):
        if use is None:
            raise ValueError("Whether to use a proxy or not must be specified!")
        self.config['Cloudflare']['use-proxy'] = str(use)

    @property
    def logging_file(self) -> str:
        return self.config['Logging']['file']

    @logging_file.setter
    def logging_file(self, file: str):
        if file is None:
            warnings.warn("No data will be logged to any file!")
        self.config['Logging']['file'] = file

    @property
    def logging_level(self) -> int:
        return logging.getLevelName(self.config['Logging']['level'])

    @logging_level.setter
    def logging_level(self, level: Union[int, str]):
        if isinstance(level, str):
            level = logging.getLevelName(level)
        if level not in VALID_LOGGING_LEVELS:
            raise ValueError("Logging level is not valid!")
        self.config['Logging']['level'] = logging.getLevelName(level)

    @property
    def pid_file(self) -> str:
        return self.config['Service']['pid-file']

    @pid_file.setter
    def pid_file(self, file: str):
        if file is None:
            raise ValueError("PID file must be provided!")
        self.config['Service']['pid-file'] = file

    def reload(self):
        self.config.read(self.file)

    def save(self):
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)