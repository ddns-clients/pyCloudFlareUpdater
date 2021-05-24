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
from typing import Union, Optional
import os
import base64
import asyncio
import keyring
import binascii

_init_called = False
_kdf_event = asyncio.Event()
_keyring = asyncio.Event()
_crypto_lock = asyncio.Lock()
_kdf = None


async def init_crypto():
    global _init_called, _kdf

    async with _crypto_lock:
        if _init_called:
            return
        _init_called = True
        from keyrings.cryptfile.cryptfile import CryptFileKeyring
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes

        _kr = CryptFileKeyring()
        _key = os.getenv("KEYRING_CRYPTPASSWD")
        if _key is None:
            raise AttributeError('Missing environment variable "KEYRING_CRYPTPASSWD"!')
        _kr.keyring_key = _key
        keyring.set_keyring(_kr)
        _keyring.set()

        _kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(), length=64, salt=os.urandom(32), iterations=100000
        )
        _kdf_event.set()


async def save_to_kr(
    identifier: str, password: Union[str, bytes], service: str = "system"
):
    if not _init_called:
        raise ValueError(
            '"init_crypto" must be called before "save_to_kr" ' "invocation"
        )
    await _keyring.wait()
    if isinstance(password, str):
        password = password.encode("ascii")
    password = base64.b64encode(password).decode("ascii")
    keyring.set_password(service, identifier, password)


async def read_from_kr(identifier: str, service: str = "system") -> Optional[bytes]:
    if not _init_called:
        raise ValueError(
            '"init_crypto" must be called before "read_from_kr" ' "invocation"
        )
    await _keyring.wait()
    b64passwd = keyring.get_password(service, identifier)
    if b64passwd is None:
        return None
    return base64.b64decode(b64passwd, validate=True)


async def gen_key() -> bytes:
    if not _init_called:
        raise ValueError('"init_crypto" must be called before "gen_key" ' "invocation")
    await _kdf_event.wait()
    return base64.urlsafe_b64encode(_kdf.derive(os.urandom(32)))


def encrypt(message: bytes, key: bytes) -> bytes:
    from cryptography.fernet import Fernet

    message = base64.b64encode(message)
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    from cryptography.fernet import Fernet

    message = Fernet(key).decrypt(token)
    return base64.b64decode(message, validate=True)


def is_valid_token(token: bytes, key: bytes) -> bool:
    from cryptography.fernet import InvalidToken

    try:
        decrypt(token, key)
        return True
    except (InvalidToken, binascii.Error):
        return False
