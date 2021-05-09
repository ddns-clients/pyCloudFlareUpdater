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
import os
from typing import Optional, TypeVar

Path = TypeVar("Path", str, bytes, os.PathLike)


def ensure_permissions(path: Path,
                       perms: int,
                       dir_fd: Optional[int] = None) -> bool:
    st = os.stat(path, dir_fd=dir_fd)
    return bool(st.st_mode & perms)


def change_permissions(path: Path,
                       perms: int,
                       dir_fd=None):
    os.chown(path, os.geteuid(), os.getegid(), dir_fd=dir_fd)
    os.chmod(path, perms, dir_fd=dir_fd)