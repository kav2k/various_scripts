#!/usr/bin/env python3
#
# MOTD script to inform users on login of upcoming system maintenance
# To be placed in /etc/update-motd.d/
# Config file read from /etc/maintenance
#
# Python 3.4 version (for Ubuntu 14.04)
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


if len(sys.argv) > 1:
    # Debugging
    CONFIG_FILE = sys.argv[1]
else:
    CONFIG_FILE = "/etc/maintenance.conf"


def datetime2str(dt, date=True):
    if date:
        return "{year:d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}".format(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute
        )
    else:
        return "{hour:02d}:{minute:02d}".format(
            hour=dt.hour,
            minute=dt.minute
        )


def print_upcoming(start, end, remaining, extra, highlight):
    sequence = ""

    if highlight:
        sequence = "\033[31;1m"

    start_string = datetime2str(start)
    end_string = datetime2str(end, date=(start.date() == end.date()))

    print("{}Upcoming maintenance in {}, from {} to {}.\033[0m".format(
        sequence,
        estimate(remaining),
        start_string,
        end_string
    ))

    if len(extra):
        if highlight:
            sequence = "\033[31m"
        print("\n{}{}\033[0m\n".format(sequence, extra))


def print_ongoing(start, end, extra):
    start_string = datetime2str(start)
    end_string = datetime2str(end, date=(start.date() != end.date()))

    print("\033[31;1;5mOngoing\033[25m maintenance from {} to {}.\033[0m".format(
        start_string,
        end_string
    ))
    if len(extra):
        print("\n\033[31m{}\033[0m\n".format(extra))


def estimate(interval):
    assert interval.total_seconds() >= 0

    days = interval.total_seconds() // (360 * 24) / 10  # type: float
    hours = interval.total_seconds() // 360 / 10  # type: float
    minutes = interval.total_seconds() // 6 / 10  # type: float
    seconds = interval.total_seconds()

    def human_round(num):
        num = round(num * 2) / 2

        if num.is_integer() or num > 10:
            return int(num)
        else:
            return num

    def plural(num):
        if human_round(num) == 1:
            return ""
        else:
            return "s"

    if days >= 1:
        return "~{} day{}".format(human_round(days), plural(days))
    elif hours >= 1:
        return "~{} hour{}".format(human_round(hours), plural(hours))
    elif minutes >= 1:
        return "~{} minute{}".format(human_round(minutes), plural(minutes))
    else:
        return "~{} second{}".format(seconds, plural(seconds))


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
    period = config.getint("config", "period")
    highlight_period = config.getint("config", "highlight_period", fallback=0)

    # Sanity check
    if start > end:
        raise ValueError("Start time older than end time")

    # No maintenance scheduled
    if end < now:
        exit()

    if start < now:
        print_ongoing(start, end, extra)
    elif remaining < timedelta(hours=period):
        highlight = remaining < timedelta(hours=highlight_period)
        print_upcoming(start, end, remaining, extra, highlight=highlight)

except ValueError as e:
    print("Error reading maintenance configuration: " + e.args[0], file=sys.stderr)
    exit(1)
