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
from keyrings.cryptfile.cryptfile import CryptFileKeyring
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from typing import Union, Optional
from os import getenv
import os
import base64
import keyring
import binascii

_kr = CryptFileKeyring()
_key = getenv('KEYRING_CRYPTPASSWD')
if _key is None:
    raise AttributeError('Missing environment variable "KEYRING_CRYPTPASSWD"!')
_kr.keyring_key = _key
keyring.set_keyring(_kr)

_kdf = PBKDF2HMAC(
    algorithm=hashes.SHA512(),
    length=64,
    salt=os.urandom(32),
    iterations=100000
)


def save_to_kr(identifier: str,
               password: Union[str, bytes],
               service: str = 'system'):
    if isinstance(password, str):
        password = password.encode('ascii')
    password = base64.b64encode(password).decode('ascii')
    keyring.set_password(service, identifier, password)


def read_from_kr(identifier: str, service: str = 'system') -> Optional[bytes]:
    b64passwd = keyring.get_password(service, identifier)
    if b64passwd is None:
        return None
    return base64.b64decode(b64passwd, validate=True)


def gen_key() -> bytes:
    return base64.urlsafe_b64encode(_kdf.derive(os.urandom(32)))


def encrypt(message: bytes, key: bytes) -> bytes:
    message = base64.b64encode(message)
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    message = Fernet(key).decrypt(token)
    return base64.b64decode(message, validate=True)


def is_valid_token(token: bytes, key: bytes) -> bool:
    try:
        msg = Fernet(key).decrypt(token)
        base64.b64decode(msg, validate=True)
        return True
    except (InvalidToken, binascii.Error):
        return False
