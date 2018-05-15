#!/usr/bin/env python3
#
# MOTD script to inform users on login of upcoming system maintenance
# To be placed in /etc/update-motd.d/
# Config file read from /etc/maintenance
#
# Requires Python 3.5+ due to PEP 484
# Version 1.0
#
# Copyright (c) 2018 Alexander Kashev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import configparser
from datetime import datetime, timedelta
from os import access, R_OK
from os.path import isfile
import sys
from typing import Union


if len(sys.argv) > 1:
    # Debugging
    CONFIG_FILE = sys.argv[1]
else:
    CONFIG_FILE = "/etc/maintenance.conf"


def print_message(start: datetime, end: datetime, remaining: timedelta, extra: str) -> None:
    print("Upcoming maintenance in {}, from {} to {}.".format(
        estimate(remaining),
        start.isoformat(sep=" "),
        end.isoformat(sep=" ")
    ))
    if len(extra):
        print(extra)


def estimate(interval: timedelta) -> str:
    assert interval.total_seconds() >= 0

    days = interval.total_seconds() // (360 * 24) / 10  # type: float
    hours = interval.total_seconds() // 360 / 10  # type: float
    minutes = interval.total_seconds() // 6 / 10  # type: float
    seconds = interval.total_seconds()

    def human_round(num: float) -> Union[int, float]:
        num = round(num * 2) / 2

        if num.is_integer() or num > 10:
            return int(num)
        else:
            return num

    if days >= 1:
        return "~{} day(s)".format(human_round(days))
    elif hours >= 1:
        return "~{} hour(s)".format(human_round(hours))
    elif minutes >= 1:
        return "~{} minute(s)".format(human_round(minutes))
    else:
        return "~{} second(s)".format(seconds)


try:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if not isfile(CONFIG_FILE) or not access(CONFIG_FILE, R_OK):
        raise ValueError("Config file not readable")

    start = datetime.strptime(config.get("maintenance", "start"), "%Y-%m-%d %H:%M")
    end = datetime.strptime(config.get("maintenance", "end"), "%Y-%m-%d %H:%M")
    now = datetime.now()
    remaining = start - now  # type: timedelta

    extra = config.get("maintenance", "extra", fallback="")

    if start > end:
        raise ValueError("Start time older than end time")

    if end < now:
        exit()

    if remaining < timedelta(hours=config.getint("config", "period")):
        print_message(start, end, remaining, extra)
except ValueError as e:
    print("Error reading maintenance configuration: " + e.args[0], file=sys.stderr)
    exit(1)
