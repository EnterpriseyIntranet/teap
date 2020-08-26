import configparser
import logging


def get_config_parsed_ldap_ini():
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read('ldap.ini')
    return config


def get_special_rooms():
    config = get_config_parsed_ldap_ini()
    if "ROOMS" in config.sections():
        return dict(config["ROOMS"].items())
    else:
        return dict()


def get_groups_to_fill():
    config = get_config_parsed_ldap_ini()
    ret = dict()
    if "TEAMS" in config.sections():
        ret["teams"] = config["TEAMS"].items()
    return ret


def _spec_to_uids(edap, spec):
    components = spec.split("+")
    members = set()
    for c in components:
        qualifier, name = c.split("=", 1)
        if qualifier == "ou":
            members.update(edap.get_uids_member_of_ou(name))
        elif qualifier == "uid":
            members.add(name)
        elif qualifier == "team":
            team_entry = edap.get_team(name)
            team_members = [x.decode("utf-8") for x in team_entry["memberUid"]]
            members.update(team_members)
        else:
            msg = f"Invalid subject to add: '{qualifier}'"
            raise RuntimeError(msg)
    logging.info(f"Translated '{spec}' into: {members}")
    return members


def _ensure_that_groups_exist(rocket, group_names):
    for name in group_names:
        g = rocket.get_group_by_name(name)
        if not g:
            rocket.create_group(name)


def _add_users_to_group(rocket, group_id, usernames):
    for username in usernames:
        rocket_user = rocket.get_user_by_username(username)
        if not rocket_user:
            logging.info(f"Couldn't find user '{username}'")
            continue
        r = rocket.invite_user_to_group(group_id, rocket_user["_id"])
        if not r.ok:
            logging.info(f"Couldn't add user '{username}': {r.reason}")


def _kick_users_from_group(rocket, group_id, usernames):
    for username in usernames:
        rocket_user = rocket.get_user_by_username(username)
        if not rocket_user:
            logging.info(f"Couldn't find user '{username}'")
            continue
        r = rocket.kick_user_from_group(group_id, rocket_user["_id"])
        if not r.ok:
            logging.info(f"Couldn't remove user '{username}': {r.reason}")


def _sync_users_in_special_rooms(rocket, group_name, intended_members):
    _ensure_that_groups_exist(rocket, [group_name])
    g = rocket.get_group_by_name(group_name)
    if not g:
        raise RuntimeError(f"Unable to create group '{group_name}'")

    current_members = {x["username"] for x in get_members_of(rocket, g["_id"])}
    new_members = intended_members.difference(current_members)
    invalid_members = current_members.difference(intended_members)

    logging.info(f"g {group_name}: current: {current_members}, adding {new_members}, removing {invalid_members}")

    _add_users_to_group(rocket, g["_id"], new_members)
    _kick_users_from_group(rocket, g["_id"], invalid_members)


def get_franchises_mn_dn(edap):
    all_franchises_records = edap.get_franchises()
    entries = [
            (struct["cn"][0].decode("utf-8"), struct["description"][0].decode("utf-8"))
            for struct in all_franchises_records]
    return entries


def get_members_of_franchise(edap, code):
    return edap.get_uids_member_of_group("franchises", code)


def get_members_of(rocket, group_id):
    result = rocket.get_group_members(group_id)
    if not result.ok:
        msg = (
                f"Error code {result.status_code}: {result.reason}"
        )
        raise RuntimeError(msg)
    members = rocket.get_group_members(group_id).json()["members"]
    return members


def get_franchise_group_id(rocket, machine_name, display_name):
    """
    Create the group if it doesn't exist
    """
    from . import ldap
    franchise = ldap.models.Franchise(machine_name=machine_name, display_name=display_name)
    group = rocket.get_group_by_name(franchise.chat_name)
    if not group:
        franchise.create_group()
        group = rocket.get_group_by_name(franchise.chat_name)
        if not group:
            msg = (
                f"Unable to get room for franchise '{f_code}', "
                f"although it has just been created under name of {franchise.chat_name}"
            )
            raise RuntimeError(msg)
    return group["_id"]


def fill_teams(edap, teams):
    for name, spec in teams:
        intended_members = _spec_to_uids(edap, spec)
        for uid in intended_members:
            try:
                edap.make_user_member_of_team(uid, name)
            except Exception as exc:
                msg = f"Error adding {uid} to team {name}: {exc}"
                logging.error(msg)


def populate_groups(edap):
    groups_to_fill = get_groups_to_fill()
    fill_teams(edap, groups_to_fill["teams"])


def populate_special_rooms(edap, rocket):
    special_rooms = get_special_rooms()
    _ensure_that_groups_exist(rocket, special_rooms)
    for r, spec in special_rooms.items():
        intended_members = _spec_to_uids(edap, spec)
        _sync_users_in_special_rooms(rocket, r, intended_members)


def sync_franchise_rooms(edap, rocket):
    franchises = get_franchises_mn_dn(edap)
    for machine_name, display_name in franchises:
        chat_group_id = get_franchise_group_id(rocket, machine_name, display_name)
        users_already_in_franchise_room = [
                u["username"]
                for u in get_members_of(rocket, chat_group_id)]

        franchise_members = set(get_members_of_franchise(edap, machine_name))
        users_to_invite = franchise_members.difference(users_already_in_franchise_room)
        invalid_members = set(users_already_in_franchise_room).difference(franchise_members)

        logging.info(f"f {display_name}: current: {users_already_in_franchise_room}, adding {users_to_invite}, removing {invalid_members}")
        _add_users_to_group(rocket, chat_group_id, users_to_invite)
        _kick_users_from_group(rocket, chat_group_id, invalid_members)


def populate_rooms(edap, rocket):
    populate_special_rooms(edap, rocket)
    sync_franchise_rooms(edap, rocket)


def maintain(edap, rocket):
    populate_groups(edap)
    populate_rooms(edap, rocket)

    from . import ldap
    ldap.models.LdapTeam.get_international_team()
    ldap.models.LdapTeam.get_everybody_team()
