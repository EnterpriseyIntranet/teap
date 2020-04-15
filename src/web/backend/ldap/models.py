""" Models to work with ldap objects, operated by EDAP library """
from edap import ObjectDoesNotExist, ConstraintError
from nextcloud.base import Permission as NxcPermission

from .utils import EdapMixin, get_edap, get_config_divisions
from ..nextcloud.utils import get_nextcloud, get_group_folder, flush_nextcloud_ldap_cache
from ..rocket_chat import utils as rutils

# TODO: separate layer with edap from data models
NEXTCLOUD_ADMIN_GROUP = "admin"
EVERYBODY_NEXTCLOUD_GROUP_ID = 'Everybody'
GENERIC_FOLDER_PERMISSIONS = [
    (NEXTCLOUD_ADMIN_GROUP, NxcPermission.ALL),
    (EVERYBODY_NEXTCLOUD_GROUP_ID, NxcPermission.READ),
]


def _assure_folder_exists_with_permissions(nxc, folder_path, all_group_ids_permissions):

    create_folder_res = nxc.create_group_folder(folder_path)
    result = create_folder_res.is_ok
    folder_id = create_folder_res.data['id']

    for group_id, permission in all_group_ids_permissions:
        grant_everybody_access = nxc.grant_access_to_group_folder(
                folder_id, group_id)
        result = result and grant_everybody_access.is_ok

        nxc.set_permissions_to_group_folder(
                folder_id, group_id,
                str(permission.value))

    return result


class GroupChatMixin:
    """ Mixin for posix groups to work with chat channels """

    @property
    def chat_name(self):
        raise NotImplementedError

    def create_channel(self):
        """
        Create channel in chat
        Returns (dict):
        """
        channel_res = rutils.rocket_service.create_channel(channel_name=self.chat_name)
        return channel_res.json()

    def create_group(self):
        """
        Create group in chat
        Returns (dict):
        """
        group_res = rutils.rocket_service.create_group(group_name=self.chat_name)
        return group_res.json()

    def channel_exists(self):
        """
        Check if channel in chat exists
        Returns (bool):
        """
        return bool(rutils.rocket_service.get_channel_by_name(self.chat_name))

    def group_exists(self):
        """
        Check if group in chat exists
        Returns (bool):
        """
        return bool(rutils.rocket_service.get_group_by_name(self.chat_name))


class GroupFolderMixin:
    """ Mixin for posix groups to work with group folder in Nextcloud """

    @property
    def main_folder_path(self):
        raise NotImplementedError

    def create_main_folder(self):
        raise NotImplementedError

    def folder_exists(self):
        """ Check if group folder exists in Nextcloud """
        nxc = get_nextcloud()
        data = nxc.get_group_folders().data
        for _, folder_info in data.items():
            if folder_info['mount_point'] == self.main_folder_path:
                return True
        return False


class User:
    def __init__(self, uid=None, given_name=None, mail=None, surname=None, franchises=None, divisions=None,
                 teams=None, picture_bytes=b"", mail_aliases=None):
        if not mail_aliases:
            mail_aliases = []
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname
        self.franchises = franchises
        self.divisions = divisions
        self.teams = teams
        self.picture_bytes = picture_bytes
        self.mail_aliases = mail_aliases

    def delete(self, *args, **kwargs):
        pass

    def add_user_to_group(self, *args, **kwargs):
        pass


class MajorStructure(GroupFolderMixin, GroupChatMixin):

    GROUP_FOLDER = None
    DEA_GROUP_SUFFIX = None
    ENTITY_NAME = None

    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name
        self.dea_display_name = display_name + f" - {self.DEA_GROUP_SUFFIX}"

    @property
    def chat_name(self):
        return rutils.sanitize_room_name(f'{self.ENTITY_NAME}-{self.display_name}')

    @property
    def main_folder_path(self):
        return "/".join([self.GROUP_FOLDER, self.machine_name])

    def create_main_folder(self):
        """
        Create subfolder in 'Franchises' folder with read-write access to members of Franchise
        and read access for 'Everybody' team
        """
        nxc = get_nextcloud()
        self._assure_root_folder_exists(nxc)

        main_folder_permissions = GENERIC_FOLDER_PERMISSIONS + [
                (self.display_name, NxcPermission.ALL),
        ]

        result = _assure_folder_exists_with_permissions(
                nxc, self.main_folder_path, main_folder_permissions)

        return result

    def create_dea_folder(self):
        nxc = get_nextcloud()
        self._assure_private_folder_exists(nxc)

        dea_folder_permissions = [
            (NEXTCLOUD_ADMIN_GROUP, NxcPermission.ALL),
            (self.display_name, NxcPermission.READ),
        ]
        dea_folder_permissions = dea_folder_permissions + [
                (self.dea_display_name, NxcPermission.ALL),
        ]

        result = _assure_folder_exists_with_permissions(
                nxc, self.dea_folder_path, dea_folder_permissions)

        return result

    def _assure_root_folder_exists(self, nxc):
        main_folder = get_group_folder(self.GROUP_FOLDER)

        if not main_folder:
            _assure_folder_exists_with_permissions(
                nxc, self.GROUP_FOLDER, GENERIC_FOLDER_PERMISSIONS)

    def _assure_private_folder_exists(self, nxc):
        return self._assure_root_folder_exists(nxc)


class LdapMajorStructure(EdapMixin):
    def create(self):
        """ Create franchise with self.machine_name, self.display_name, create corresponding teams """
        self.add_to_edap()
        self.create_teams()
        channel_res = self.create_group()

        # create group folders
        main_folder_success = self.create_main_folder()
        dea_folder_success = self.create_dea_folder()

        return {
            'rocket': channel_res,
            'main_folder': {
                'success': main_folder_success
            },
            'dea_folder': {
                'success': dea_folder_success
            },
        }

    @staticmethod
    def _get_ldap_dict(code):
        raise NotImplementedError()

    @classmethod
    def from_ldap(cls, code):
        structure = cls._get_ldap_dict(code)
        kwargs = dict(machine_name=code, display_name=structure["description"][0].decode("UTF-8"))
        return cls(** kwargs)

    def add_user(self, uid):
        self._add_user_to_edap(uid)
        if not self.group_exists():
            self.create_group()
        if not self.folder_exists():
            self.create_main_folder()

    def add_user_dea(self, uid):
        self.add_user(uid)
        self._add_user_to_edap_dea(uid)

    def add_to_edap(self):
        raise NotImplementedError()


class LdapUser(EdapMixin, User):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapUser, self).__init__(*args, **kwargs)

    @classmethod
    def get_from_edap(cls, uid):
        ret = cls()
        edap_dict = ret.edap.get_user(uid)

        ret.uid = uid
        ret.given_name = edap_dict.get("givenName", [b""])[0].decode("UTF-8")
        ret.mail = edap_dict.get("mail", [b""])[0].decode("UTF-8")
        ret.surname = edap_dict.get("sn", [b""])[0].decode("UTF-8")
        ret.picture_bytes = edap_dict.get("jpegPhoto", [None])[0]
        ret.mail_aliases = [a.decode("UTF-8") for a in edap_dict.get("mailAlias", [b""])]
        return ret

    def __repr__(self):
        return f'<LdapUser(fqdn={self.fqdn}, uid={self.uid})>'

    def exists_in_edap(self):
        return self.edap.user_of_uid_exists(self.uid) > 0

    def add_to_edap(self, password):
        """ Create user entity in ldap """
        ret = self.edap.add_user(self.uid, self.given_name, self.surname, password, self.mail, self.picture_bytes)
        return ret

    def add_to_everybody_team(self):
        """ Add user to everybody team in edap """
        everybody_team = LdapTeam.get_everybody_team()
        ret = self.edap.make_user_member_of_team(self.uid, everybody_team.machine_name)
        return ret

    def create(self, password):
        self.add_to_edap(password)
        self.add_to_everybody_team()

        nxc = get_nextcloud()
        flush_nextcloud_ldap_cache(nxc)

        rocket_data = self.create_chat_account(password)
        return {
            'rocket': rocket_data
        }

    def modify(self, what, new_value):
        """
        Args:
            what: one of name, surname, password, mail, picture_bytes
            new_value: Plain (not raw) representation of the value.
        """
        translate = dict(
                name="givenName",
                surname="sn",
                mail="mail",
                picture_bytes="jpegPhoto",
                mail_aliases="mailAlias",
                password="userPassword",
                cn="cn",
        )
        return self.edap.modify_user(self.uid, {translate[what]: new_value})

    def sync_to_edap(self):
        """
        Sync all LDAP user attributes except password.
        """
        self.modify("name", self.given_name)
        self.modify("surname", self.surname)
        self.modify("mail", self.mail)
        self.modify("picture_bytes", self.picture_bytes)
        self.modify("mail_aliases", self.mail_aliases)
        # self.modify("cn", f"{self.given_name} {self.surname}")

    def check_password(self, password):
        """
        Args:
            password: The password to check against
        """
        return self.edap.verify_user_password(self.uid, password)

    def delete(self):
        self.remove_from_all_groups()
        res = self.edap.delete_user(self.uid)
        self.delete_chat_account()
        return res

    def remove_from_all_groups(self):
        """ Remove user from all ldap groups """
        user_groups = self.edap.get_user_groups(self.uid)
        for each in user_groups:
            self.edap.remove_uid_member_of(self.uid, each['fqdn'])

    def create_chat_account(self, password):
        """
        Create chat account for user
        Args:
            password (str):

        Returns (tuple):
            (success (bool), data (dict))
        """
        rocket_res = rutils.rocket_service.create_user(username=self.uid, password=password, email=self.mail, name=self.given_name)
        return rocket_res.json()

    def delete_chat_account(self):
        """ Delete user's chat account """
        rocket_user = rutils.rocket_service.get_user_by_username(self.uid)
        if rocket_user and rocket_user.get('_id'):
            return rutils.rocket_service.delete_user(rocket_user['_id'])

    def get_teams(self):
        """ Get teams where user is a member """
        from .serializers import edap_teams_schema
        user_teams = self.edap.get_teams(f'memberUid={self.uid}')
        return edap_teams_schema.load(user_teams)

    def add_user_to_implied_structures(self, team_machine_name):
        from .serializers import edap_franchise_schema, edap_division_schema
        franchise, division = self.edap.get_team_component_units(team_machine_name)
        franchise = edap_franchise_schema.load(franchise)
        division = edap_division_schema.load(division)
        franchise.add_user(self.uid)
        division.add_user(self.uid)

    def add_to_team(self, team_machine_name):
        """ Add user to team and to respective franchise and division groups """
        self.edap.make_user_member_of_team(self.uid, team_machine_name)

        self.add_user_to_implied_structures(team_machine_name)

    def remove_from_team(self, team_machine_name):
        """ Remove user from team """
        self.edap.remove_uid_member_of_team(self.uid, team_machine_name)

    def get_franchises(self):
        from .serializers import edap_franchises_schema
        franchises_raw = self.edap.get_franchises(f'memberUid={self.uid}')
        return edap_franchises_schema.load(franchises_raw)

    def ensure_in_franchise(self, franchise_machine_name):
        self.edap.make_user_member_of_franchise(self.uid, franchise_machine_name)
        franchise = LdapFranchise(machine_name=franchise_machine_name)

        rocket = rutils.RocketChatService()
        ids = rocket.get_ids(self.uid, group_name=franchise.chat_name)
        rocket.invite_user_to_group(
                rocket_group=ids.group,
                rocket_user=ids.user)

    def ensure_in_fdea(self, franchise_machine_name):
        self.edap.make_user_member_of_cdea(self.uid, franchise_machine_name)
        self.ensure_in_franchise(franchise_machine_name)

    def remove_from_franchise(self, franchise_machine_name):
        """ Remove user from franchise """
        self.edap.remove_uid_member_of_franchise(self.uid, franchise_machine_name)

    def get_divisions(self):
        from .serializers import edap_divisions_schema
        divisions_raw = self.edap.get_divisions(f'memberUid={self.uid}')
        return edap_divisions_schema.load(divisions_raw)

    def ensure_in_division(self, division_machine_name):
        self.edap.make_uid_member_of_division(self.uid, division_machine_name)

    def ensure_in_ddea(self, division_machine_name):
        self.edap.make_uid_member_of_ddea(self.uid, division_machine_name)
        self.ensure_in_division(division_machine_name)

    def remove_from_division(self, division_machine_name):
        """ Remove user from division """
        self.edap.remove_uid_member_of_division(self.uid, division_machine_name)


class Franchise(MajorStructure):

    GROUP_FOLDER = 'Franchises'
    DEA_GROUP_SUFFIX = "FDEA"
    ENTITY_NAME = "Franchise"

    @property
    def main_folder_path(self):
        return "/".join([self.GROUP_FOLDER, self.machine_name.upper()])

    @property
    def dea_folder_path(self):
        return "/".join([self.main_folder_path, "FD private"])


class LdapFranchise(Franchise, LdapMajorStructure):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        if "display_name" not in kwargs:
            kwargs["display_name"] = LdapFranchise.suggest_name(kwargs["machine_name"])
        super(LdapFranchise, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_ldap_dict(code):
        edap = get_edap()
        return edap.get_franchise(code)

    def __repr__(self):
        return f'<LdapFranchise(fqdn={self.fqdn})>'

    def _add_user_to_edap(self, uid):
        self.edap.make_user_member_of_franchise(uid, self.machine_name)

    def _add_user_to_edap_dea(self, uid):
        self.edap.make_user_member_of_cdea(uid, self.machine_name)

    def add_to_edap(self):
        """ Create franchise entity in ldap """
        if self.check_exists_by_display_name(self.display_name):
            raise ConstraintError('Franchise with such display name already exists')
        self.edap.create_cdea(machine_name=self.machine_name, display_name=self.dea_display_name)
        return self.edap.create_franchise(machine_name=self.machine_name, display_name=self.display_name)

    def create_teams(self):
        """
        When a new franchise is created, an LDAP entry is created for it, and team entries are created as well,
        so there are teams for every <new franchise>-<division> combination.

        Should be called when new Franchise is created
        """
        from .serializers import edap_divisions_schema
        divisions = edap_divisions_schema.load(self.edap.get_divisions())
        for division in divisions:
            machine_name = self.edap.make_team_machine_name(self.machine_name, division.machine_name)
            display_name = self.edap.make_team_display_name(self.display_name, division.display_name)
            self.edap.create_team(machine_name, display_name)

    @staticmethod
    def check_exists_by_display_name(display_name):
        """
        Check if franchise with such display name already exists

        Args:
            display_name (str): display name of franchise

        Returns (bool):
        """
        edap = get_edap()
        franchises = edap.get_franchises(f'description={display_name}')
        return bool(franchises)

    @staticmethod
    def suggest_name(franchise_machine_name):
        """
        Suggest name for franchise by it's machine name
        Args:
            franchise_machine_name (str): franchise machine name

        Returns (str):
        """
        edap = get_edap()
        labelled_name = edap.label_franchise(franchise_machine_name)
        # TODO: add logic if such display name already exists
        # if LdapFranchise.check_exists_by_display_name(labelled_name)
        #     return 'already exists'
        return labelled_name


class Division(MajorStructure):

    GROUP_FOLDER = 'Divisions'
    DEA_GROUP_SUFFIX = "DDEA"
    ENTITY_NAME = "Division"

    @property
    def main_folder_path(self):
        return "/".join([self.GROUP_FOLDER, self.display_name])

    @property
    def dea_folder_path(self):
        return "/".join([self.main_folder_path, "DD private"])


class LdapDivision(Division, LdapMajorStructure):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapDivision, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapDivision(fqdn={self.fqdn}>'

    @staticmethod
    def _get_ldap_dict(code):
        edap = get_edap()
        return edap.get_division(code)

    def _add_user_to_edap(self, uid):
        self.edap.make_uid_member_of_division(uid, self.machine_name)

    def _add_user_to_edap_dea(self, uid):
        self.edap.make_uid_member_of_ddea(uid, self.machine_name)

    def add_to_edap(self):
        """ Create division entity in ldap """
        if self.check_exists_by_display_name(self.display_name):
            raise ConstraintError('Division with such display name already exists')
        self.edap.create_ddea(machine_name=self.machine_name, display_name=self.dea_display_name)
        return self.edap.create_division(machine_name=self.machine_name, display_name=self.display_name)

    @staticmethod
    def check_exists_by_display_name(display_name):
        """
        Check if franchise with such display name already exists

        Args:
            display_name (str): display name of franchise

        Returns (bool):
        """
        edap = get_edap()
        divisions = edap.get_divisions(f'description={display_name}')
        return bool(divisions)

    def create_teams(self):
        """
         When a new division is created, an LDAP entry is created for it, and team entries are created as well,
         so there are teams for every <franchise>-<new division> combination.

         Should be called when new Franchise is created
         """
        from .serializers import edap_franchises_schema
        franchises = edap_franchises_schema.load(self.edap.get_franchises())
        for franchise in franchises:
            machine_name = self.edap.make_team_machine_name(franchise.machine_name, self.machine_name)
            display_name = self.edap.make_team_display_name(franchise.display_name, self.display_name)
            self.edap.create_team(machine_name, display_name)


class Team:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


STRING_OPERATIONS = dict(
        lowercase=lambda s: s.lower(),
        uppercase=lambda s: s.upper(),
        capitalize=lambda s: s.capitalize(),
        noop=lambda s: s,
    )


class LdapTeam(EdapMixin, Team):

    EVERYBODY_MACHINE_NAME = 'everybody'
    EVERYBODY_DISPLAY_NAME = 'Everybody'
    EVERYBODY_NEXTCLOUD_GROUP_ID = EVERYBODY_NEXTCLOUD_GROUP_ID

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        self.n_conversion_fun = STRING_OPERATIONS["noop"]
        if "nextcloud_string_operation" in kwargs:
            self.n_conversion_fun = STRING_OPERATIONS[kwargs["nextcloud_string_operation"]]
        self.EVERYBODY_NEXTCLOUD_GROUP_ID = self.n_conversion_fun(self.EVERYBODY_MACHINE_NAME)
        super(LdapTeam, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapTeam(fqdn={self.fqdn}>'

    def get_team_components(self):
        from .serializers import edap_franchise_schema, edap_division_schema
        franchise_json, division_json = self.edap.get_team_component_units(self.machine_name)
        return edap_franchise_schema.load(franchise_json), edap_division_schema.load(division_json)

    @staticmethod
    def get_everybody_team():
        """ Get or create and return 'Everybody' Team """
        from .serializers import edap_team_schema
        edap = get_edap()
        try:
            everybody_team = edap.get_team(LdapTeam.EVERYBODY_MACHINE_NAME)
        except ObjectDoesNotExist:
            edap.create_team(LdapTeam.EVERYBODY_MACHINE_NAME, LdapTeam.EVERYBODY_DISPLAY_NAME)
            everybody_team = edap.get_team(LdapTeam.EVERYBODY_MACHINE_NAME)
        return edap_team_schema.load(everybody_team)


def bootstrap_ldap():
    """ Create the basic structure """
    import edap

    e = get_edap()
    divisions = get_config_divisions()
    edap.ensure_org_sanity(e)
    for code, desc in divisions.items():
        d = LdapDivision(machine_name=code, display_name=desc)
        d.create()
