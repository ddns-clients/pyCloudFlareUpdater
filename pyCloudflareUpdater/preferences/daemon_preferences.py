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
    is_valid_token, init_crypto
)
from .. import (
    PRODUCTION_FILE_LOG_LEVEL, VALID_LOGGING_LEVELS, DEFAULT_SETTINGS,
    ensure_permissions, change_permissions, VALID_RECORD_TYPES
)
from configupdater import ConfigUpdater, Section, Option
from cryptography.fernet import InvalidToken
from ..utils.cache import cached, ucached
from ..utils.str import is_none_or_empty
from typing import Union, Optional, Any
from argparse import Namespace
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
    v = config.get(option, str(default))
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

    def __init__(self):
        if self.__must_init:
            self.config = ConfigUpdater()
            self._ck: Optional[bytes] = None
            self.__cache__ = {}
            self.__must_init = False

    @classmethod
    async def create_from_args(cls, p_args: Namespace) -> 'Preferences':
        self = Preferences()
        await init_crypto()
        await self._init(domain=p_args.domain,
                         name=p_args.name,
                         rtype=p_args.type,
                         ttl=p_args.ttl,
                         update_time=p_args.time,
                         key=p_args.key,
                         mail=p_args.mail,
                         use_proxy=p_args.proxied,
                         pid_file=p_args.pid_file,
                         log_file=p_args.log_file,
                         log_level=p_args.log_level)
        return self

    async def _init(self,
                    domain: str = None,
                    name: str = None,
                    rtype: str = None,
                    ttl: int = None,
                    update_time: int = None,
                    key: str = None,
                    mail: str = None,
                    use_proxy: bool = False,
                    pid_file: str = None,
                    log_file: str = None,
                    log_level: int = PRODUCTION_FILE_LOG_LEVEL):
        self.config = ConfigUpdater()
        if not os.path.exists(self.file):
            await self.create_empty_file()
        self.config.read(self.file)
        ck = read_from_kr('cloudflare-key')
        home = Path.home()
        uid = os.geteuid()
        log_file = \
            log_file or "/var/log/cloudflare-ddns.log" if uid == 0 \
                else f"{home}/log/cloudflare-ddns.log"
        pid_file = \
            pid_file or "/var/run/cloudflare-ddns.pid" if uid == 0 \
                else f"{home}/.cache/cloudflare-ddns.pid"

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

        save_task = None
        ck = await ck
        if ck is None:
            ck = await gen_key()
            save_task = save_to_kr('cloudflare-key', ck)
        self._ck = ck

        error_base = '"%s" must be defined and cannot be empty!'

        self.domain = get_or_error(cloudflare,
                                   'domain',
                                   error_base % 'Domain',
                                   default=domain)
        self.name = get_or_error(cloudflare,
                                 'name',
                                 error_base % 'Record (name)',
                                 default=name)
        self.type = get_or_error(cloudflare,
                                 'type',
                                 error_base % 'Record (type)',
                                 default=rtype)
        self.ttl = int(get_or_error(cloudflare,
                                    'ttl',
                                    error_base % 'TTL (Time To Live)',
                                    default=ttl))
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
        self.save()

        if save_task is not None:
            await save_task

    def _check_perms(self):
        if not ensure_permissions(self.file, 0o700):
            warnings.warn("Insecure permissions detected! Changing...")
            change_permissions(self.file, 0o700)

    @property
    @cached('__cache__')
    def domain(self) -> str:
        return self.config['Cloudflare']['domain'].value

    @domain.setter
    @ucached('__cache__')
    def domain(self, new_domain: str):
        if new_domain is None:
            raise ValueError("Domain must be provided!")
        self.config['Cloudflare']['domain'].value = new_domain

    @property
    @cached('__cache__')
    def name(self) -> str:
        return self.config['Cloudflare']['name'].value

    @name.setter
    @ucached('__cache__')
    def name(self, new_name: str):
        if new_name is None:
            raise ValueError("Record's name must be provided!")
        self.config['Cloudflare']['name'].value = new_name

    @property
    @cached('__cache__')
    def type(self) -> str:
        return self.config['Cloudflare']['type'].value

    @type.setter
    @ucached('__cache__')
    def type(self, new_type: str):
        if new_type is None:
            raise ValueError("Record's type must be provided!")
        if new_type not in VALID_RECORD_TYPES:
            raise ValueError(f"Record type '{new_type}' is not a valid value! "
                             "Available options are: "
                             f"{sorted(VALID_RECORD_TYPES)}")
        self.config['Cloudflare']['type'].value = new_type

    @property
    @cached('__cache__')
    def ttl(self) -> int:
        return int(self.config['Cloudflare']['ttl'].value)

    @ttl.setter
    @ucached('__cache__')
    def ttl(self, new_ttl: int):
        if new_ttl is None:
            raise ValueError('TTL value must be provided!')
        if new_ttl < 1:
            raise ValueError("TTL must be, at least, '1' (automatic) or bigger")
        self.config['Cloudflare']['ttl'].value = str(new_ttl)

    @property
    @cached('__cache__')
    def frequency(self) -> int:
        return int(self.config['Cloudflare']['frequency-minutes'].value)

    @frequency.setter
    @ucached('__cache__')
    def frequency(self, new_freq: int):
        if new_freq is None:
            raise ValueError("Update frequency must be provided")
        self.config['Cloudflare']['frequency-minutes'].value = str(new_freq)

    @property
    @cached('__cache__')
    def key(self) -> str:
        apikey = self.config['Cloudflare']['api-key'].value
        key = self._ck
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
        key = self._ck
        if key is None:
            raise AttributeError('Key was not created! Unexpected failure')
        if not is_valid_token(new_key.encode(), key):
            new_key = encrypt(new_key.encode(), key).decode()
        self.config['Cloudflare']['api-key'].value = new_key

    @property
    @cached('__cache__')
    def mail(self) -> str:
        return self.config['Cloudflare']['mail'].value

    @mail.setter
    @ucached('__cache__')
    def mail(self, new_mail: str):
        if new_mail is None:
            raise ValueError("Mail must be provided!")
        self.config['Cloudflare']['mail'].value = new_mail

    @property
    @cached('__cache__')
    def use_proxy(self) -> bool:
        return bool(self.config['Cloudflare']['use-proxy'].value)

    @use_proxy.setter
    @ucached('__cache__')
    def use_proxy(self, use: bool):
        if use is None:
            raise ValueError("Whether to use a proxy or not must be specified!")
        self.config['Cloudflare']['use-proxy'].value = str(use)

    @property
    @cached('__cache__')
    def logging_file(self) -> str:
        return self.config['Logging']['file'].value

    @logging_file.setter
    @ucached('__cache__')
    def logging_file(self, file: str):
        if file is None:
            warnings.warn("No data will be logged to any file!")
        self.config['Logging']['file'].value = file

    @property
    @cached('__cache__')
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
    @cached('__cache__')
    def pid_file(self) -> str:
        return self.config['Service']['pid-file'].value

    @pid_file.setter
    @ucached('__cache__')
    def pid_file(self, file: str):
        if file is None:
            raise ValueError("PID file must be provided!")
        self.config['Service']['pid-file'].value = file

    async def reload(self):
        self.__cache__ = {}
        self._check_perms()
        self.config.read(self.file)

    async def save_async(self):
        self.save()

    def save(self):
        self._check_perms()
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)

    @staticmethod
    async def create_empty_file() -> bool:
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
