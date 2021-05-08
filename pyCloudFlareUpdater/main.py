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
from pathlib import Path
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from argparse import SUPPRESS
from logging import getLogger
from time import sleep
from pwd import getpwnam
from grp import getgrnam
from .logging_utils import init_logging
from .preferences import Preferences
from .network import Cloudflare
from .network import get_machine_public_ip
from .values import description
import os
import daemon
import lockfile
import signal
import traceback


def main(preferences: Preferences):
    log = LoggingHandler(logs=[getLogger("cloudflareLogger")])
    loop_continuation = True
    try:
        net = Cloudflare(domain=preferences.get_domain(),
                         name=preferences.get_name(),
                         key=preferences.get_key(),
                         mail=preferences.get_mail(),
                         proxied=preferences.is_record_behind_proxy())
        while loop_continuation:
            current_ip = get_machine_public_ip()
            log.info("Current machine IP: \"{0}\"".format(current_ip))
            if preferences.get_latest_ip() == "0.0.0.0":
                preferences.set_latest_ip(net.get_cloudflare_latest_ip())
                log.warning(
                    "User saved latest IP is not up to date - downloading Cloudflare A Record value: \"{0}\""
                        .format(preferences.get_latest_ip()))
            if preferences.get_latest_ip() != current_ip:
                log.info("IP needs an upgrade - OLD IP: {0} | NEW IP: {1}"
                         .format(preferences.get_latest_ip(), current_ip))
                result = net.set_cloudflare_ip(current_ip)
                log.info(
                    "IP updated correctly! - Operation return code: {0}".format(
                        result))
                log.debug("Updating saved IP...")
                preferences.set_latest_ip(current_ip)
            else:
                log.info("IP has not changed - skipping")
            if not preferences.is_running_as_daemon():
                log.info("This script is only executed once. Finishing...")
                loop_continuation = False
            else:
                log.info("Next check in about {0} minute{1}"
                         .format((preferences.get_time() / 60),
                                 's' if (
                                                preferences.get_time() / 60) > 1 else ''))
                sleep(preferences.get_time())
    except KeyboardInterrupt:
        log.warning("Received SIGINT - exiting...")
    except Exception as e:
        log.error("Exception registered! - " + str(e))
        log.error("Stacktrace: " + traceback.format_exc())
    finally:
        preferences.save_preferences()
        exit(0)


def parser():
    args = ArgumentParser(description=description,
                          allow_abbrev=False)
    args.add_argument("--domain",
                      type=str,
                      default=None,
                      help="Cloudflare domain to be updated.")
    args.add_argument("--A",
                      type=str,
                      default=None,
                      help="Cloudflare 'A' Record name.")
    args.add_argument("--time",
                      type=int,
                      default=5,
                      help="Time (in minutes) to check for updated IP "
                           "(defaults: 5 min.) - must be higher than 0.")
    args.add_argument("--key",
                      type=str,
                      default=None,
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
    args.add_argument("--pidfile",
                      type=str,
                      default=SUPPRESS,
                      metavar="PID FILE",
                      help="Specifies a custom PID file for storing current "
                           "daemon PID.")
    args.add_argument("--logfile",
                      type=str,
                      default=SUPPRESS,
                      metavar="LOG FILE",
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
                      metavar="GROUP NAME",
                      help="Run the daemon as the specified group.")
    p_args = args.parse_args()
    preferences = Preferences(domain=p_args.domain,
                              A=p_args.A,
                              update_time=p_args.time,
                              key=p_args.key,
                              mail=p_args.mail,
                              use_proxy=p_args.proxied,
                              pid_file=p_args.pidfile,
                              log_file=p_args.log_file)

    log = init_logging('cloudflare-logger',
                       log_file=preferences.logging_file,
                       file_level=preferences.logging_level)
    fds = []
    for handler in log.handlers:
        if isinstance(handler, RotatingFileHandler):
            fds += handler.stream.fileno()

    uid = getpwnam(p_args.user) if p_args.user is not None else None
    gid = getgrnam(p_args.group) if p_args.group is not None else None

    pid_file = lockfile.LockFile(preferences.pid_file)

    def handle_sigterm():
        try:
            log.warning('SIGTERM received! Finishing...')
            preferences.save()
            pid_file.break_lock()
            os.remove(pid_file.path)
            log.warning('Cloudflare DDNS finished correctly')
            for handler in log.handlers:
                handler.close()
            exit(0)
        except Exception as e:
            log.fatal('Unable to finish correctly! - %s', e, exc_info=True)
            exit(1)

    context = daemon.DaemonContext(
        working_directory=Path.home(),
        umask=0o002,
        pidfile=pid_file,
        files_preserve=fds,
        signal_map={
            signal.SIGTERM: handle_sigterm,
            signal.SIGHUP: 'terminate',
            signal.SIGUSR1: preferences.reload
        },
        uid=uid,
        gid=gid
    )

    with context:
        main(preferences)
