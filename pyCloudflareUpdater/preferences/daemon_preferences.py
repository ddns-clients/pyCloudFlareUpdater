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
from .crypt import (
    save_to_kr, read_from_kr, gen_key, encrypt, decrypt,
    is_valid_token
)
from .. import (
    PRODUCTION_FILE_LOG_LEVEL, VALID_LOGGING_LEVELS, DEFAULT_SETTINGS,
    ensure_permissions, change_permissions
)
from configupdater import ConfigUpdater, Section, Option
from cryptography.fernet import InvalidToken
from ..utils.str import is_none_or_empty
from typing import Union, Optional, Any
from pathlib import Path
import os
import logging
import warnings


def get_or_error(config: Section,
                 option: str,
                 error_msg: str,
                 default: Optional[Any] = None):
    if option not in config:
        raise KeyError(error_msg)
    v = config.get(option, default)
    if v is not None and isinstance(v, Option) and is_none_or_empty(v.value):
        if default is None:
            raise ValueError(error_msg)
        v = default
    return v.value if isinstance(v, Option) else v


class Preferences:
    __instance__ = None
    file = "%s/.config/cloudflare-ddns.ini" % Path.home()

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
            self.config = ConfigUpdater()
            if not os.path.exists(self.file):
                self.create_empty_file()
            self.config.read(self.file)
            self._ck = read_from_kr('cloudflare-key')
            if self._ck is None:
                self._ck = gen_key()
                save_to_kr('cloudflare-key', self._ck)
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

            error_base = '"%s" must be defined and cannot be empty!'

            self.domain = get_or_error(cloudflare,
                                       'domain',
                                       error_base % 'Domain',
                                       default=domain)
            self.name = get_or_error(cloudflare,
                                     'name',
                                     error_base % 'A-Record (name)',
                                     default=name)
            self.frequency = int(get_or_error(cloudflare,
                                              'frequency-minutes',
                                              error_base % 'Frequency',
                                              default=update_time))
            self.key = get_or_error(cloudflare,
                                    'api-key',
                                    error_base % 'API Key',
                                    default=key)
            self.mail = get_or_error(cloudflare,
                                     'mail',
                                     error_base % 'Mail',
                                     default=mail)
            self.use_proxy = bool(get_or_error(cloudflare,
                                               'use-proxy',
                                               error_base % 'Proxied',
                                               default=str(use_proxy)))

            self.logging_file = get_or_error(log,
                                             'file',
                                             error_base % 'Log file',
                                             default=log_file)
            self.logging_level = get_or_error(log,
                                              'level',
                                              error_base % 'Logging level',
                                              logging.getLevelName(log_level))

            self.pid_file = get_or_error(service,
                                         'pid-file',
                                         error_base % 'PID file',
                                         default=pid_file)

            with open(self.file, 'w') as configfile:
                self.config.write(configfile)

    def _check_perms(self):
        if not ensure_permissions(self.file, 0o700):
            warnings.warn("Insecure permissions detected! Changing...")
            change_permissions(self.file, 0o700)

    @property
    def domain(self) -> str:
        return self.config['Cloudflare']['domain'].value

    @domain.setter
    def domain(self, new_domain: str):
        if new_domain is None:
            raise ValueError("Domain must be provided!")
        self.config['Cloudflare']['domain'].value = new_domain

    @property
    def name(self) -> str:
        return self.config['Cloudflare']['name'].value

    @name.setter
    def name(self, new_A: str):
        if new_A is None:
            raise ValueError("'A' record must be provided!")
        self.config['Cloudflare']['name'].value = new_A

    @property
    def frequency(self) -> int:
        return int(self.config['Cloudflare']['frequency-minutes'].value)

    @frequency.setter
    def frequency(self, new_freq: int):
        if new_freq is None:
            raise ValueError("Update frequency must be provided")
        self.config['Cloudflare']['frequency-minutes'].value = str(new_freq)

    @property
    def key(self) -> str:
        apikey = self.config['Cloudflare']['api-key'].value
        key = read_from_kr('cloudflare-key')
        if key is None:
            raise AttributeError('Key was not created! Unexpected failure')
        try:
            return decrypt(apikey.encode(), key).decode()
        except InvalidToken:
            self.key = apikey
            return apikey

    @key.setter
    def key(self, new_key: str):
        if new_key is None:
            raise ValueError("API key must be provided!")
        key = read_from_kr('cloudflare-key')
        if key is None:
            raise AttributeError('Key was not created! Unexpected failure')
        if not is_valid_token(new_key.encode(), key):
            new_key = encrypt(new_key.encode(), key).decode()
        self.config['Cloudflare']['api-key'].value = new_key

    @property
    def mail(self) -> str:
        return self.config['Cloudflare']['mail'].value

    @mail.setter
    def mail(self, new_mail: str):
        if new_mail is None:
            raise ValueError("Mail must be provided!")
        self.config['Cloudflare']['mail'].value = new_mail

    @property
    def use_proxy(self) -> bool:
        return bool(self.config['Cloudflare']['use-proxy'].value)

    @use_proxy.setter
    def use_proxy(self, use: bool):
        if use is None:
            raise ValueError("Whether to use a proxy or not must be specified!")
        self.config['Cloudflare']['use-proxy'].value = str(use)

    @property
    def logging_file(self) -> str:
        return self.config['Logging']['file'].value

    @logging_file.setter
    def logging_file(self, file: str):
        if file is None:
            warnings.warn("No data will be logged to any file!")
        self.config['Logging']['file'].value = file

    @property
    def logging_level(self) -> int:
        return logging.getLevelName(self.config['Logging']['level'].value)

    @logging_level.setter
    def logging_level(self, level: Union[int, str]):
        if isinstance(level, str):
            level = logging.getLevelName(level)
        if level not in VALID_LOGGING_LEVELS:
            raise ValueError("Logging level is not valid!")
        self.config['Logging']['level'].value = logging.getLevelName(level)

    @property
    def pid_file(self) -> str:
        return self.config['Service']['pid-file'].value

    @pid_file.setter
    def pid_file(self, file: str):
        if file is None:
            raise ValueError("PID file must be provided!")
        self.config['Service']['pid-file'].value = file

    def reload(self):
        self._check_perms()
        self.config.read(self.file)

    def save(self):
        self._check_perms()
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)

    @staticmethod
    def create_empty_file() -> bool:
        if not os.path.exists(Preferences.file):
            config_dir = os.path.dirname(Preferences.file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, mode=0o700, exist_ok=True)

            with open(Preferences.file, 'w') as configfile:
                configfile.write(DEFAULT_SETTINGS)

            if not ensure_permissions(Preferences.file, 0o700):
                change_permissions(Preferences.file, 0o700)

            return True
        return False
