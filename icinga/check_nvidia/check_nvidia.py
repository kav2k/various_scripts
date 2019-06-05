#!/usr/bin/env python3
#
# Icinga/Nagios check script to monitor status and temperatures of Nvidia GPUs via nvidia-smi
#
# Requires Python 3 and module nagiosplugin (package python3-nagios or python3-nagiosplugin)
# Also requires a working nvidia-smi install
# Version 1.0
#
# Copyright (c) 2019 Alexander Kashev
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

"""Icinga check for Nvidia GPU status"""

import nagiosplugin
import argparse
import logging
import subprocess
import xml.etree.ElementTree as ET
import re
from functools import reduce

_log = logging.getLogger("nagiosplugin")


class NvidiaResource(nagiosplugin.Resource):
    def parse_temp(self, text):
        match = re.search(r"(\d+) C", text)
        if match:
            return float(match.group(1))
        else:
            return None

    def parse_percent(self, text):
        match = re.search(r"(\d+) %", text)
        if match:
            return float(match.group(1))
        else:
            return None

    def parse_MiB(self, text):
        match = re.search(r"(\d+) MiB", text)
        if match:
            return float(match.group(1))
        else:
            return None

    def probe(self):
        metrics = []

        try:
            output = subprocess.check_output(["nvidia-smi", "-q", "-x"])

            data = ET.fromstring(output)
            gpus = [gpu for gpu in data.findall("gpu")]

            temps = [
                self.parse_temp(gpu.find("./temperature/gpu_temp").text)
                for gpu in gpus
            ]

            metrics.extend([
                nagiosplugin.Metric("GPU {} Temp".format(idx), temp, min=0, context="gpu_temp")
                for idx, temp in enumerate(temps)
            ])

            loads = [
                self.parse_percent(gpu.find("./utilization/gpu_util").text)
                for gpu in gpus
            ]

            metrics.extend([
                nagiosplugin.Metric(
                    "GPU {} Load".format(idx),
                    load,
                    "%",
                    min=0, max=100,
                    context="gpu_util"
                )
                for idx, load in enumerate(loads)
            ])

            mem_loads = [
                (
                    self.parse_MiB(gpu.find("./fb_memory_usage/used").text),
                    self.parse_MiB(gpu.find("./fb_memory_usage/total").text),
                )
                for gpu in gpus
            ]

            metrics.extend([
                nagiosplugin.Metric(
                    "GPU {} Mem".format(idx),
                    load * 1024 * 1024,
                    "B",
                    min=0, max=(total * 1024 * 1024),
                    context="gpu_util"
                )
                for idx, (load, total) in enumerate(mem_loads)
            ])

        except subprocess.CalledProcessError as cpe:
            _log.info("Error in nvidia-smi")
            _log.info(cpe.returncode)

            metrics = [
                nagiosplugin.Metric(
                    "nvidia-smi error",
                    "Non-zero return code",
                    context="data_error"
                )
            ]
        except ET.ParseError:
            _log.info("Error parsing nvidia-smi output")

            metrics = [
                nagiosplugin.Metric(
                    "nvidia-smi error",
                    "Can't parse XML output",
                    context="data_error"
                )
            ]

        return metrics


class DataErrorContext(nagiosplugin.Context):
    def evaluate(self, metric, resource):
        return nagiosplugin.Result(nagiosplugin.Critical, metric.value)


class NvidiaSummary(nagiosplugin.Summary):
    def ok(self, results):
        def is_temp(context):
            if context.name == 'gpu_temp':
                return 1
            else:
                return 0

        return "All {} GPUs healthy".format(
            reduce(
                lambda count, r: count + is_temp(r.context),
                results, 0
            )
        )


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='60',
                      help='return warning if GPU temperature is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='80',
                      help='return critical if GPU temperatureis outside RANGE')
    argp.add_argument('-v', '--verbose', action='count', default=0)
    args = argp.parse_args()
    check = nagiosplugin.Check(
        NvidiaResource(),
        nagiosplugin.ScalarContext('gpu_temp', args.warning, args.critical),
        nagiosplugin.ScalarContext('gpu_util'),
        DataErrorContext('data_error'),
        NvidiaSummary()
    )
    check.name = "NVIDIA"
    check.main(args.verbose)


if __name__ == '__main__':
    main()
