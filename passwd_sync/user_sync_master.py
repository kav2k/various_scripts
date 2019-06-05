#!/usr/bin/env python3

import os
import user_sync

DIR = "/home/configuration/user_sync/"

os.system("pwck -s")
os.system("grpck -s")

(passwd, shadow) = user_sync.read_pair("/etc/passwd", "/etc/shadow", user_sync.is_user)
(group, gshadow) = user_sync.read_pair("/etc/group", "/etc/gshadow", user_sync.is_user)

changed = user_sync.write(DIR + "passwd.master", passwd)
changed = user_sync.write(DIR + "shadow.master", shadow) or changed
changed = user_sync.write(DIR + "group.master", group) or changed
changed = user_sync.write(DIR + "gshadow.master", gshadow) or changed

if changed:
    print("Changes applied")
else:
    print("No changes")
