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
from logging import DEBUG, INFO, WARNING
import logging

DESCRIPTION = """pyCloudflareUpdater\n\n
The first time this application is executed, all params must be included in order to save the user preferences 
and do this process automatically."""
CLOUDFLARE_BASE_URL = "https://api.cloudflare.com/client/v4/{0}"

# Logging constants
LOGGER_NAME = "cloudflare:logger"
LOG_FILE = "cloudflare-ddns.log"
LOG_DEFAULT_FORMAT = \
    "%(process)d[%(thread)d] - %(asctime)s | [%(levelname)s]: %(message)s"
PRODUCTION_CONSOLE_LOG_LEVEL = INFO
PRODUCTION_FILE_LOG_LEVEL = WARNING

DEV_CONSOLE_LOG_LEVEL = DEBUG
DEV_FILE_LOG_LEVEL = DEBUG

VALID_LOGGING_LEVELS = {logging.DEBUG, logging.WARN, logging.INFO,
                        logging.CRITICAL, logging.ERROR, logging.FATAL,
                        logging.NOTSET}

# Preferences settings
DEFAULT_SETTINGS = """
[Logging]
# Log file to append/create logs. Recommended using a custom folder
# as old logs are periodically compressed and saved at the same location.
#
# Defaults: ~/log/cloudflare-ddns.log (when non root)
# Defaults: /var/log/cloudflare-ddns.log (when root)
file = 
# Level to use when logging messages. Available options are:
# DEBUG, INFO, WARNING, CRITICAL, FATAL, ERROR, NOTSET.
#
# Defaults: WARNING 
level = 

[Cloudflare]
# In dash.cloudflare.com, domain name to update.
domain =
# The record to update. As this is a DDNS client, it is suggested to
# update de 'A' Record (but a CNAME is also OK).
name = 
# The minimum frequency when checking for updates, in minutes.
#
# Defaults: 1 (minute)
frequency-minutes = 
# The private API key used when communicating with Cloudflare services for
# updating/querying the stored values.
# Store here the API key and, when the service starts, will be encrypted
# using a secure random password.
api-key =
# The login email used when accessing Cloudflare.
mail =
# After updating the specified name record, sets it to be proxied through
# Cloudflare or not (direct connection).
#
# Defaults: False
use-proxy =

[Service]
# The PID file used when running the service for storing current PID
# (Program IDentifier). This allows the system to start, stop, restart and
# reload the service when necessary.
#
# Defaults: ~/.cache/cloudflare-ddns.pid (when non root)
# Defaults: /var/run/cloudflare-ddns.pid (when root)
pid-file =
"""
