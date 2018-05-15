#!/bin/bash

MOTD_LEVEL=96

if [ ! -d "/etc/update-motd.d" ]; then
    echo 'No /etc/update-motd.d, does your system support it?'
    exit 1
fi

PY3="/usr/bin/env python3"

IS_35=`$PY3 -c 'import sys; print(sys.version_info >= (3,5))'`
IS_34=`$PY3 -c 'import sys; print(sys.version_info >= (3,4))'`

if [ $IS_35 = "True" ]; then
    echo 'Installing Python 3.5+ version'
    install ./maintenance.py /etc/update-motd.d/$MOTD_LEVEL-maintenance
    install -b ./maintenance.conf /etc/maintenance.conf
    exit 0
fi

if [ $IS_34 = "True" ]; then
    echo 'Installing Python 3.4 version'
    install ./maintenance-3_4.py /etc/update-motd.d/$MOTD_LEVEL-maintenance
    install -b ./maintenance.conf /etc/maintenance.conf
    exit 0
fi

echo 'No compatible Python 3 version found'
exit 1
