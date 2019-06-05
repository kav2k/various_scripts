import os


def get_id(line):
    return line.split(":")[2]


def get_name(line):
    return line.split(":")[0]


def is_user(obj_id):
    return (int(obj_id) >= 1000) and (int(obj_id) < 60000)


def is_system(obj_id):
    return not is_user(obj_id)


def read_pair(db, shadow_db, criterion=(lambda x: True)):
    with open(db) as passwd_file:
        passwd = [line.strip() for line in passwd_file.readlines() if criterion(get_id(line))]
        users = [get_name(line) for line in passwd]
    with open(shadow_db) as shadow_file:
        shadow = [line.strip() for line in shadow_file.readlines() if get_name(line) in users]
    return (passwd, shadow)


def write(name, lines):
    data = "\n".join(lines)
    if os.path.isfile(name):
        with open(name) as old:
            old_data = old.read()
            if old_data == data:
                return False

    old_umask = os.umask(0o77)
    with open(name, "w") as out:
        out.write("\n".join(lines))
    os.umask(old_umask)
    return True
