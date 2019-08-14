""" Models to work with ldap objects, operated by EDAP library """
from edap import ObjectDoesNotExist, ConstraintError
from nextcloud.base import Permission as NxcPermission

from .utils import EdapMixin, get_edap
from ..nextcloud.utils import get_nextcloud, get_group_folder
from ..rocket_chat.utils import rocket_service

# TODO: separate layer with edap from data models
NEXTCLOUD_ADMIN_GROUP = "admin"


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
        channel_res = rocket_service.create_channel(channel_name=self.chat_name)
        return channel_res.json()

    def channel_exists(self):
        """
        Check if franchise channel in chat exists
        Returns (bool):
        """
        return bool(rocket_service.get_channel_by_name(self.chat_name))


class GroupFolderMixin:
    """ Mixin for posix groups to work with group folder in Nextcloud """

    @property
    def folder_path(self):
        raise NotImplementedError

    def create_folder(self):
        raise NotImplementedError

    def folder_exists(self):
        """ Check if group folder exists in Nextcloud """
        nxc = get_nextcloud()
        data = nxc.get_group_folders().data
        for _, folder_info in data.items():
            if folder_info['mount_point'] == self.folder_path:
                return True
        return False


class User:
    def __init__(self, uid=None, given_name=None, mail=None, surname=None, groups=None, franchises=None, divisions=None,
                 teams=None):
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname
        self.groups = groups  # TODO: groups are separated for franchises, divisions, teams, so delete
        self.franchises = franchises
        self.divisions = divisions
        self.teams = teams

    def delete(self, *args, **kwargs):
        pass

    def add_user_to_group(self, *args, **kwargs):
        pass


class LdapUser(EdapMixin, User):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapUser, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapUser(fqdn={self.fqdn}, uid={self.uid})>'

    def exists_in_edap(self):
        return self.edap.user_of_uid_exists(self.uid) > 0

    def add_to_edap(self, password):
        """ Create user entity in ldap """
        return self.edap.add_user(self.uid, self.given_name, self.surname, password, self.mail)

    def add_to_everybody_team(self):
        """ Add user to everybody team in edap """
        everybody_team = LdapTeam.get_everybody_team()
        return self.edap.make_user_member_of_team(self.uid, everybody_team.machine_name)

    def create(self, password):
        self.add_to_edap(password)
        self.add_to_everybody_team()
        rocket_data = self.create_chat_account(password)
        return {
            'rocket': rocket_data
        }

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
        rocket_res = rocket_service.create_user(username=self.uid, password=password, email=self.mail, name=self.given_name)
        return rocket_res.json()

    def delete_chat_account(self):
        """ Delete user's chat account """
        rocket_user = rocket_service.get_user_by_username(self.uid)
        if rocket_user and rocket_user.get('_id'):
            return rocket_service.delete_user(rocket_user['_id'])

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

    def remove_from_franchise(self, franchise_machine_name):
        """ Remove user from franchise """
        self.edap.remove_uid_member_of_franchise(self.uid, franchise_machine_name)

    def get_divisions(self):
        from .serializers import edap_divisions_schema
        divisions_raw = self.edap.get_divisions(f'memberUid={self.uid}')
        return edap_divisions_schema.load(divisions_raw)

    def ensure_in_division(self, division_machine_name):
        self.edap.make_uid_member_of_division(self.uid, division_machine_name)

    def remove_from_division(self, division_machine_name):
        """ Remove user from division """
        self.edap.remove_uid_member_of_division(self.uid, division_machine_name)


class Franchise(GroupChatMixin, GroupFolderMixin):

    GROUP_FOLDER = 'Franchises'

    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name

    def _sanitize_room_name(self):
        import re
        name = re.sub(" ", "-", self.display_name)
        name = re.sub("&", "and", name)
        return name

    @property
    def chat_name(self):
        room_name = self._sanitize_room_name()
        return f'Franchise-{room_name}'.replace(' ', '-')

    @property
    def folder_path(self):
        return "/".join([Franchise.GROUP_FOLDER, self.machine_name])

    def create_folder(self):
        """
        Create subfolder in 'Franchises' folder with read-write access to members of Franchise
        and read access for 'Everybody' team
        """
        nxc = get_nextcloud()
        main_franchises_folder = get_group_folder(Franchise.GROUP_FOLDER)

        if not main_franchises_folder:
            Franchise.create_main_folder()

        create_folder_res = nxc.create_group_folder(self.folder_path)
        folder_id = create_folder_res.data['id']

        grant_access_res = nxc.grant_access_to_group_folder(
                folder_id, self.machine_name)
        grant_everybody_access = nxc.grant_access_to_group_folder(
                folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID)
        nxc.grant_access_to_group_folder(
                folder_id, NEXTCLOUD_ADMIN_GROUP)

        nxc.set_permissions_to_group_folder(
                folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID,
                str(NxcPermission.READ.value))

        return create_folder_res.is_ok and grant_access_res.is_ok and grant_everybody_access.is_ok

    @staticmethod
    def create_main_folder():
        """
        Create main 'Franchises' folder in root directory
        with read rights for 'Everybody' team
        """
        nxc = get_nextcloud()
        create_main_folder_res = nxc.create_group_folder(Franchise.GROUP_FOLDER)

        main_folder_id = create_main_folder_res.data['id']

        nxc.grant_access_to_group_folder(
                main_folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID)
        nxc.grant_access_to_group_folder(
                main_folder_id, NEXTCLOUD_ADMIN_GROUP)

        nxc.set_permissions_to_group_folder(
                main_folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID,
                str(NxcPermission.READ.value))


class LdapFranchise(EdapMixin, Franchise):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapFranchise, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapFranchise(fqdn={self.fqdn})>'

    def create(self):
        """ Create franchise with self.machine_name, self.display_name, create corresponding teams """
        self.add_to_edap()
        self.create_teams()
        # create group folder
        folder_success = self.create_folder()
        channel_res = self.create_channel()
        return {
            'rocket': channel_res,
            'folder': {
                'success': folder_success
            }
        }

    def add_to_edap(self):
        """ Create franchise entity in ldap """
        if LdapFranchise.check_exists_by_display_name(self.display_name):
            raise ConstraintError('Franchise with such display name already exists')
        return self.edap.create_franchise(machine_name=self.machine_name, display_name=self.display_name)

    def add_user(self, uid):
        self.edap.make_user_member_of_franchise(uid, self.machine_name)
        if not self.channel_exists():
            self.create_channel()
        if not self.folder_exists():
            self.create_folder()

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


class Division(GroupChatMixin, GroupFolderMixin):

    GROUP_FOLDER = 'Divisions'

    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name

    @property
    def chat_name(self):
        return f'Division-{self.display_name}'.replace(' ', '-')

    @property
    def folder_path(self):
        return "/".join([self.GROUP_FOLDER, self.display_name])

    def create_folder(self):
        """
        Create subfolder in 'Divisions' folder with read-write access to members of Division
        and read access for 'Everybody' team
        """
        nxc = get_nextcloud()
        main_folder = get_group_folder(Division.GROUP_FOLDER)

        if not main_folder:
            Division.create_main_folder()

        create_folder_res = nxc.create_group_folder(self.folder_path)
        folder_id = create_folder_res.data['id']

        grant_access_res = nxc.grant_access_to_group_folder(
                folder_id, self.machine_name)
        grant_everybody_access = nxc.grant_access_to_group_folder(
                folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID)
        nxc.grant_access_to_group_folder(
                folder_id, NEXTCLOUD_ADMIN_GROUP)

        nxc.set_permissions_to_group_folder(
                folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID,
                str(NxcPermission.READ.value))

        return create_folder_res.is_ok and grant_access_res.is_ok and grant_everybody_access.is_ok

    @staticmethod
    def create_main_folder():
        """
        Create main 'Divisions' folder in root directory
        with read rights for 'Everybody' team
        """
        nxc = get_nextcloud()
        create_main_folder_res = nxc.create_group_folder(Division.GROUP_FOLDER)

        main_folder_id = create_main_folder_res.data['id']

        nxc.grant_access_to_group_folder(
                main_folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID)
        nxc.grant_access_to_group_folder(
                main_folder_id, NEXTCLOUD_ADMIN_GROUP)

        nxc.set_permissions_to_group_folder(
                main_folder_id, LdapTeam.EVERYBODY_NEXTCLOUD_GROUP_ID,
                str(NxcPermission.READ.value))


class LdapDivision(EdapMixin, Division):
    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapDivision, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapDivision(fqdn={self.fqdn}>'

    def add_to_edap(self):
        """ Add division entity to edap """
        return self.edap.create_division(self.machine_name, display_name=self.display_name)

    def create(self):
        """ Create division with self.machine_name, self.display_name, create corresponding teams """
        self.add_to_edap()
        self.create_teams()
        folder_success = self.create_folder()
        channel_res = self.create_channel()
        return {
            'rocket': channel_res,
            'folder': {
                'success': folder_success
            }
        }

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

    def add_user(self, uid):
        self.edap.make_uid_member_of_division(uid, self.machine_name)
        if not self.channel_exists():
            self.create_channel()
        if not self.folder_exists():
            self.create_folder()


class Team:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapTeam(EdapMixin, Team):

    EVERYBODY_MACHINE_NAME = 'everybody'
    EVERYBODY_DISPLAY_NAME = 'Everybody'
    EVERYBODY_NEXTCLOUD_GROUP_ID = 'Everybody'

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
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
