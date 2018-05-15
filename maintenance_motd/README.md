# Maintenance announcement MOTD

A Python 3 script to accounce next maintenance in a dynamic MOTD.

Requires update-motd (`/etc/update-motd.d/`) and Python 3.4+ on the target system.

Run `install.sh` as root to install:

* MOTD script `/etc/update-motd.d/96-maintenance`
* Config file `/etc/maintenance.conf`

Existing config file will be backed up as `/etc/maintenance.conf~`
