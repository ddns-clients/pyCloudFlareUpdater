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
from logging import DEBUG, INFO, WARNING
import logging

DESCRIPTION = """pyCloudFlareUpdater\n\n
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
