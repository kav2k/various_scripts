A poor man's substitute for LDAP
======

A script to copy non-system records from `passwd` / `shadow` / `group` / `gshadow` on one machine ("master")
    and merge them with system records on other machines ("node").

System / non-system record is defined by UID range (currently an Ubuntu-compatible range 1000-59999 is considered "non-system").

1. Place scripts into a shared folder between machines, adjust DIR constants in `user_sync_master.py` and `user_sync_node.py`.
2. Run `user_sync_master.py` on source machine.
3. Run `user_sync_node.py` on target machines. It is safe to do in parallel if hostnames differ.

In short: just use LDAP already.
