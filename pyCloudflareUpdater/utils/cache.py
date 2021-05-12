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
from typing import Optional, Any, Callable


def cached(cached_prop: str):
    def cache_decorator(func: Callable[[Any], Optional[Any]]):
        def wrapper(self):
            d = getattr(self, cached_prop)
            key = func.__name__
            if key not in d or d.get(key, None) is None:
                res = func(self)
                if res is not None:
                    d[key] = res
                return res
            return d[key]
        return wrapper
    return cache_decorator


def ucached(cached_prop: str):
    def cache_decorator(func: Callable[[Any, Any], None]):
        def wrapper(self, new_value):
            d = getattr(self, cached_prop)
            key = func.__name__
            d[key] = new_value
            func(self, new_value)
        return wrapper
    return cache_decorator
