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
from logging.handlers import RotatingFileHandler
from typing import Awaitable, Callable, Any
from argparse import ArgumentParser
from colorama import Back, Style
from logging import Logger
from pathlib import Path
from pwd import getpwnam
from grp import getgrnam
from .logging_utils import init_logging
from .preferences import Preferences
from .network import Cloudflare, get_machine_public_ip
from .utils import (
    DESCRIPTION, LOGGER_NAME, PROJECT_URL, DEVELOPER_MAIL,
    VALID_RECORD_TYPES
)
import daemon
import daemon.pidfile
import socket
import signal
import traceback
import requests
import asyncio


def launch(fn: Callable[..., Awaitable[Any]], *args, **kwargs):
    routine = fn(*args, **kwargs)
    asyncio.run(routine)


async def main(preferences: Preferences,
               log: Logger,
               single_run: bool = False):
    continue_running = True
    exit_code = 0
    try:
        cloudflare = Cloudflare(preferences)
        while continue_running:
            try:
                latest_ip = await cloudflare.ip
                current_ip = await get_machine_public_ip()
                log.info("Current machine IP: \"{0}\"".format(current_ip))
                if current_ip != latest_ip:
                    log.warning(f'IP changed! {latest_ip} -> {current_ip}')
                    cloudflare.ip = current_ip

            except socket.gaierror:
                log.warning('DNS name resolution failure! Check settings')
            except requests.exceptions.HTTPError as httperr:
                log.critical('HTTP error when accessing '
                             f'{httperr.request}!\n{httperr}')
            finally:
                if single_run:
                    log.info('User requested single run. Exiting...')
                    break
                await asyncio.sleep(preferences.frequency)
    except KeyboardInterrupt:
        log.warning("Received SIGINT - exiting...")
        exit_code = 130
    except Exception as e:
        log.fatal(f'Unexpected exception registered! "{str(e)}"')
        log.fatal(f'Please, submit the following traceback at {PROJECT_URL} '
                  f'or email it at {DEVELOPER_MAIL}')
        log.fatal("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Stacktrace:\n"
                  f"{traceback.format_exc()}\n"
                  "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        exit_code = 1
    finally:
        await preferences.save_async()
        exit(exit_code)


async def parser():
    args = ArgumentParser(prog='cloudflare-ddns',
                          description=DESCRIPTION,
                          allow_abbrev=False)
    args.add_argument("--domain",
                      type=str,
                      default=None,
                      help="Cloudflare domain to be updated.")
    args.add_argument("--name",
                      metavar='RECORD NAME',
                      type=str,
                      default=None,
                      help="Cloudflare Record's name to update.")
    args.add_argument("--type",
                      metavar="RECORD TYPE",
                      default='A',
                      help="Cloudflare Record's type to update. "
                           "Defaults to 'A'",
                      choices=sorted(VALID_RECORD_TYPES))
    args.add_argument("--ttl",
                      default=1,
                      type=int,
                      help="DNS record's TTL (Time To Live) value. Defaults "
                           "to '1' (automatic)")
    args.add_argument("--time",
                      type=int,
                      default=5,
                      help="Time (in minutes) to check for updated IP "
                           "(defaults: 5 min.) - must be higher than 0.")
    args.add_argument("--key",
                      type=str,
                      default=None,
                      metavar='API-KEY',
                      help="Cloudflare API key.")
    args.add_argument("--mail",
                      type=str,
                      default=None,
                      help="Cloudflare sign-in mail.")
    args.add_argument("--proxied",
                      action="store_true",
                      default=False,
                      help="Set this value if you want your 'A' Record to be "
                           "behind the Cloudflare proxy "
                           "(disabled by default).")
    args.add_argument("--no-daemonize",
                      action="store_true",
                      default=False,
                      help="By default, the program runs as a daemon in "
                           "background. With this option enabled, "
                           "the program will run only once and then exit.")
    args.add_argument("--init-config",
                      action="store_true",
                      default=False,
                      help="Creates the configuration file at the specific "
                           "location with no contents but the keys with no"
                           "values (ready to be full-filled). When this "
                           "option is set, the program creates the file and "
                           "exits.")
    args.add_argument("--config-file",
                      type=str,
                      default=f"{Path.home()}/.config/cloudflare-ddns.ini",
                      metavar="PATH",
                      help="Defines the daemon's config file location. "
                           "Defaults to: \"~/.config/cloudflare-ddns.ini\"")
    args.add_argument("--pid-file",
                      type=str,
                      default=None,
                      metavar="LOCATION",
                      help="Specifies a custom PID file for storing current "
                           "daemon PID.")
    args.add_argument("--log-file",
                      type=str,
                      default=None,
                      metavar="LOCATION",
                      help="Specifies a custom LOG file for storing current "
                           "daemon logs.")
    args.add_argument("--user",
                      type=str,
                      default=None,
                      metavar="USERNAME",
                      help="Run the daemon as the specified user.")
    args.add_argument("--group",
                      type=str,
                      default=None,
                      metavar="GROUP-NAME",
                      help="Run the daemon as the specified group.")
    p_args = args.parse_args()
    try:
        Preferences.file = p_args.config_file
        if p_args.init_config:
            if await Preferences.create_empty_file():
                print(f'Created configuration file at "{Preferences.file}"')
                exit(0)
            else:
                print('File already exists! Not doing anything...')
                exit(1)

        preferences = await Preferences.create_from_args(p_args)

        log = init_logging(LOGGER_NAME,
                           log_file=preferences.logging_file,
                           file_level=preferences.logging_level)
        fds = []
        for handler in log.handlers:
            if isinstance(handler, RotatingFileHandler):
                fds.append(handler.stream.fileno())

        uid = getpwnam(p_args.user) if p_args.user is not None else None
        gid = getgrnam(p_args.group) if p_args.group is not None else None

        pid_file = daemon.pidfile.PIDLockFile(preferences.pid_file)

        def handle_sigterm(*_):
            try:
                log.warning('SIGTERM received! Finishing...')
                preferences.save()
                log.info('Cloudflare DDNS finished correctly')
                for handler in log.handlers:
                    handler.close()
                exit(0)
            except Exception as e:
                log.fatal(f'Unable to finish correctly! - {e}',
                          exc_info=True)
                exit(1)
            finally:
                pid_file.break_lock()

        context = daemon.DaemonContext(
            working_directory=Path.home(),
            umask=0o002,
            pidfile=pid_file,
            files_preserve=fds,
            signal_map={
                signal.SIGTERM: handle_sigterm,
                signal.SIGHUP: handle_sigterm,
                signal.SIGUSR1: lambda *_: log.warning(
                    'Reloading preferences!') and preferences.reload()
            },
            uid=uid,
            gid=gid
        )

        with context:
            launch(main, preferences, log, single_run=p_args.no_daemonize)
    except Exception as err:
        try:
            log.fatal(str(err))
        except NameError:
            pass
        finally:
            print(f"{Back.RED}Error: {str(err)}{Style.RESET_ALL}")
            exit(1)
