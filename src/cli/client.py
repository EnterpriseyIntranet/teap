import argparse
import configparser

import nextcloud


class Credentials(object):
    user = ""
    url = ""
    password = ""

    @staticmethod
    def from_dict(d):
        result = Credentials()

        result.url = d["url"]
        result.user = d.get("user")
        result.password = d["password"]

        return result


def read_credentials(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    assert "credentials" in config
    creds = config["credentials"]
    return Credentials.from_dict(creds)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "credentials",
        help="Ini file with admin username/password."
    )

    s = parser.add_subparsers()

    _add_user = s.add_parser("add_user")
    _add_user.add_argument("user")
    _add_user.add_argument("password")
    _add_user.add_argument("--group", "-g", default=[], action="append")
    _add_user.set_defaults(func=add_user)

    _rm_user = s.add_parser("rm_user")
    _rm_user.add_argument("user")
    _rm_user.set_defaults(func=remove_user)

    _ls_user = s.add_parser("list_users")
    _ls_user.set_defaults(func=list_users)

    return parser.parse_args()


def remove_user(args, nxc):
    user_id = args.user
    rm_user_res = nxc.delete_user(user_id)
    assert rm_user_res.is_ok


def list_users(args, nxc):
    res = nxc.get_users()
    print("code: ", res.status_code)
    assert res.is_ok
    print(res.data["users"])


def add_user(args, nxc):
    new_user_id = args.user
    add_user_res = nxc.add_user(new_user_id, args.password)
    assert add_user_res.is_ok

    all_groups_res = nxc.get_groups()
    assert all_groups_res.is_ok
    all_groups = set(all_groups_res.data["groups"])

    for group in args.group:
        if group not in all_groups:
            add_group_res = nxc.add_group(group)
            assert add_group_res.is_ok, \
                f"Failed to add group {group}: {add_group_res.status_code}"
        add_to_group_res = nxc.add_to_group(new_user_id, group)
        assert add_to_group_res.is_ok, \
            f"Failed to add group {group}: {add_to_group_res.status_code}"


def main():
    args = parse_args()

    creds = read_credentials(args.credentials)
    nxc = nextcloud.NextCloud(
        endpoint=creds.url, user=creds.user, password=creds.password,
        json_output=True)

    args.func(args, nxc)


if __name__ == "__main__":
    main()
