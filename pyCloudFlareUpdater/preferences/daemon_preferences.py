#                             pyCloudFlareUpdater
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
                 A: str = None,
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
                    else "%s/logs/cloudflare-ddns.log" % home
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
                self.config['Logging'] = {
                    'File': log_file,
                    'Level': logging.getLevelName(log_level)
                }
            if 'Cloudflare' not in self.config:
                self.config['Cloudflare'] = {
                    'Domain': domain,
                    'A': A,
                    'FrequencySeconds': update_time,
                    'APIKey': key,
                    'Mail': mail,
                    'Proxy': use_proxy
                }
            if 'Service' not in self.config:
                self.config['Service'] = {
                    'PID': pid_file
                }

            cloudflare = self.config['Cloudflare']
            log = self.config['Logging']
            service = self.config['Service']

            self.domain = cloudflare.get('Domain', domain)
            self.A = cloudflare.get('A', A)
            self.frequency = int(
                cloudflare.get('FrequencySeconds', update_time))
            self.key = cloudflare.get('APIKey', key)
            self.mail = cloudflare.get('Mail', mail)
            self.use_proxy = bool(cloudflare.get('Proxy', str(use_proxy)))

            self.logging_file = log.get('File', log_file)
            self.logging_level = \
                log.get('Level', logging.getLevelName(log_level))

            self.pid_file = service.get('PID', pid_file)

            with open(self.file, 'r') as configfile:
                self.config.write(configfile)

    @property
    def domain(self) -> str:
        return self.config['Cloudflare']['Domain']

    @domain.setter
    def domain(self, new_domain: str):
        if new_domain is None:
            raise ValueError("Domain must be provided!")
        self.config['Cloudflare']['Domain'] = new_domain

    @property
    def A(self) -> str:
        return self.config['Cloudflare']['A']

    @A.setter
    def A(self, new_A: str):
        if new_A is None:
            raise ValueError("'A' record must be provided!")
        self.config['Cloudflare']['A'] = new_A

    @property
    def frequency(self) -> int:
        return int(self.config['Cloudflare']['FrequencySeconds'])

    @frequency.setter
    def frequency(self, new_freq: int):
        if new_freq is None:
            raise ValueError("Update frequency must be provided")
        self.config['Cloudflare']['FrequencySeconds'] = str(new_freq)

    @property
    def key(self) -> str:
        return self.config['Cloudflare']['APIKey']

    @key.setter
    def key(self, new_key: str):
        if new_key is None:
            raise ValueError("API key must be provided!")
        self.config['Cloudflare']['APIKey'] = new_key

    @property
    def mail(self) -> str:
        return self.config['Cloudflare']['Mail']

    @mail.setter
    def mail(self, new_mail: str):
        if new_mail is None:
            raise ValueError("Mail must be provided!")
        self.config['Cloudflare']['Mail'] = new_mail

    @property
    def use_proxy(self) -> bool:
        return bool(self.config['Cloudflare']['Proxy'])

    @use_proxy.setter
    def use_proxy(self, use: bool):
        if use is None:
            raise ValueError("Whether to use a proxy or not must be specified!")
        self.config['Cloudflare']['Proxy'] = str(use)

    @property
    def logging_file(self) -> str:
        return self.config['Logging']['File']

    @logging_file.setter
    def logging_file(self, file: str):
        if file is None:
            warnings.warn("No data will be logged to any file!")
        self.config['Logging']['File'] = file

    @property
    def logging_level(self) -> int:
        return logging.getLevelName(self.config['Logging']['Level'])

    @logging_level.setter
    def logging_level(self, level: Union[int, str]):
        if isinstance(level, str):
            level = logging.getLevelName(level)
        if level not in VALID_LOGGING_LEVELS:
            raise ValueError("Logging level is not valid!")
        self.config['Logging']['Level'] = logging.getLevelName(level)

    @property
    def pid_file(self) -> str:
        return self.config['Service']['PID']

    @pid_file.setter
    def pid_file(self, file: str):
        if file is None:
            raise ValueError("PID file must be provided!")
        self.config['Service']['PID'] = file

    def reload(self):
        self.config.read(self.file)

    def save(self):
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)

    def __del__(self):
        self.save()
