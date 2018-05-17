#!/usr/bin/env python3
#
# Icinga/Nagios check script to report if a reboot is needed for some updates on Debian-based systems.
#
# Supports Nagios conventions for warning/critical ranges of time since reboot was first required.
# Stores state in /tmp/reboot-required.cookie
# Reports the list of packages that require reboot in verbose mode.
#
# Requires Python 3 and module nagiosplugin (package python3-nagios or python3-nagiosplugin)
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

"""Icinga check for Debian/Ubuntu reboot requirement"""

import nagiosplugin
import argparse
import os
import logging
import datetime

_log = logging.getLogger("nagiosplugin")

COOKIE_FILE = "/tmp/reboot-required.cookie"


class RebootRequired(nagiosplugin.Resource):
    def probe(self):
        with nagiosplugin.Cookie(COOKIE_FILE) as cookie:
            if os.path.isfile("/run/reboot-required"):
                _log.info("reboot-required file found")

                timestamp = cookie.get('timestamp', default=os.path.getmtime("/run/reboot-required"))
                cookie['timestamp'] = timestamp

                file_age = datetime.datetime.now().timestamp() - timestamp

                try:
                    with open("/run/reboot-required.pkgs") as file:
                        _log.info("reboot-required.pkgs file read")
                        packages = set(file.read().splitlines())
                        _log.info(packages)
                except Exception:
                    packages = None
                return [
                    nagiosplugin.Metric('age', file_age, uom="s"),
                    nagiosplugin.Metric('packages', packages)
                ]
            else:
                cookie.pop('timestamp', None)

                _log.info("File not found")
                return [
                    nagiosplugin.Metric('age', 0, uom="s"),
                    nagiosplugin.Metric('packages', set())
                ]


class PackagesContext(nagiosplugin.Context):
    def performance(self, metric, resource):
        return nagiosplugin.Performance("packages", len(metric.value))


class RebootRequiredSummary(nagiosplugin.Summary):
    def ok(self, results):
        return "Not required"

    def problem(self, results):
        # Round off the microseconds
        delta = datetime.timedelta(seconds=results["age"].metric.value)
        delta = delta - datetime.timedelta(microseconds=delta.microseconds)

        return "Required for {} packages since at least {}".format(
            len(results["packages"].metric.value),
            delta
        )

    def verbose(self, results):
        if len(results["packages"].metric.value):
            package_list = map(
                lambda name: "* {}".format(name),
                sorted(results["packages"].metric.value)
            )
            return ["Packages requiring update:"] + list(package_list)


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='0',
                      help='return warning if reboot_required file age is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='604800',
                      help='return critical if reboot_required file age is outside RANGE')
    argp.add_argument('-v', '--verbose', action='count', default=0)
    args = argp.parse_args()
    check = nagiosplugin.Check(
        RebootRequired(),
        nagiosplugin.ScalarContext('age', args.warning, args.critical),
        PackagesContext('packages'),
        RebootRequiredSummary()
    )
    check.name = "REBOOT_REQUIRED"
    check.main(args.verbose)


if __name__ == '__main__':
    main()
