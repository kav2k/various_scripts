#!/usr/bin/env python3

import os
import socket
import filecmp
import user_sync

DIR = "/home/configuration/user_sync/"

os.system("pwck -s")
os.system("grpck -s")

(passwd, shadow) = user_sync.read_pair("/etc/passwd", "/etc/shadow", user_sync.is_system)
(passwd_master, shadow_master) = user_sync.read_pair(DIR + "passwd.master", DIR + "shadow.master")
passwd.extend(passwd_master)
shadow.extend(shadow_master)

(group, gshadow) = user_sync.read_pair("/etc/group", "/etc/gshadow", user_sync.is_system)
(group_master, gshadow_master) = user_sync.read_pair(DIR + "group.master", DIR + "gshadow.master")
group.extend(group_master)
gshadow.extend(gshadow_master)

node = socket.gethostname()

user_sync.write(DIR + "passwd." + node, passwd)
user_sync.write(DIR + "shadow." + node, shadow)
user_sync.write(DIR + "group." + node, group)
user_sync.write(DIR + "gshadow." + node, gshadow)

os.system("pwck -s {} {}".format(DIR + "passwd." + node, DIR + "shadow." + node))
os.system("grpck -s {} {}".format(DIR + "group." + node, DIR + "gshadow." + node))

changed = not filecmp.cmp("/etc/passwd", DIR + "passwd." + node)
changed = not filecmp.cmp("/etc/shadow", DIR + "shadow." + node) or changed
changed = not filecmp.cmp("/etc/group", DIR + "group." + node) or changed
changed = not filecmp.cmp("/etc/gshadow", DIR + "gshadow." + node) or changed

if changed:
    os.system("cppw " + DIR + "passwd." + node)
    os.system("cppw -s " + DIR + "shadow." + node)
    os.system("cpgr " + DIR + "group." + node)
    os.system("cpgr -s " + DIR + "gshadow." + node)

    print("Changes applied")
else:
    print("No changes")
