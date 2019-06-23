""" Models to work with ldap objects, operated by EDAP library """
from edap import ObjectDoesNotExist, ConstraintError
from nextcloud.base import Permission as NxcPermission

from .utils import EdapMixin, get_edap
from backend.nextcloud.utils import get_nextcloud, get_group_folder

# TODO: separate layer with edap from data models


class User:
    def __init__(self, uid, given_name=None, mail=None, surname=None, groups=None, franchises=None, divisions=None,
                 teams=None):
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname
        self.groups = groups  # TODO: groups are separated for franchises, divisions, teams, so delete
        self.franchises = franchises
        self.divisions = divisions
        self.teams = teams

    def delete_user(self, *args, **kwargs):
        pass

    def add_user_to_group(self, *args, **kwargs):
        pass


class LdapUser(EdapMixin, User):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapUser, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapUser(fqdn={self.fqdn}, uid={self.uid})>'

    def create(self, password):
        self.edap.add_user(self.uid, self.given_name, self.surname, password)

        for group in self.groups:
            self.edap.make_uid_member_of(self.uid, group)

        # add user to 'Everybody' team
        everybody_team = LdapTeam.get_everybody_team()
        self.edap.make_user_member_of_team(self.uid, everybody_team.machine_name)

    def get_teams(self):
        """ Get teams where user is a member """
        from .serializers import edap_teams_schema
        user_teams = self.edap.get_teams(f'memberUid={self.uid}')
        return edap_teams_schema.load(user_teams).data

    def add_to_team(self, team_machine_name):
        """ Add user to team and to respective franchise and division groups """
        from .serializers import edap_franchise_schema, edap_division_schema
        self.edap.make_user_member_of_team(self.uid, team_machine_name)
        franchise, division = self.edap.get_team_component_units(team_machine_name)
        franchise = edap_franchise_schema.load(franchise).data
        division = edap_division_schema.load(division).data
        self.edap.make_user_member_of_franchise(self.uid, franchise.machine_name)
        self.edap.make_uid_member_of_division(self.uid, division.machine_name)

    def remove_from_team(self, team_machine_name):
        """ Remove user from team """
        self.edap.remove_uid_member_of_team(self.uid, team_machine_name)

    def get_franchises(self):
        from .serializers import edap_franchises_schema
        franchises_raw = self.edap.get_franchises(f'memberUid={self.uid}')
        return edap_franchises_schema.load(franchises_raw).data

    def add_to_franchise(self, franchise_machine_name):
        """ Add user to franchise """
        self.edap.make_user_member_of_franchise(self.uid, franchise_machine_name)

    def remove_from_franchise(self, franchise_machine_name):
        """ Remove user from franchise """
        self.edap.remove_uid_member_of_franchise(self.uid, franchise_machine_name)

    def get_divisions(self):
        from .serializers import edap_divisions_schema
        divisions_raw = self.edap.get_divisions(f'memberUid={self.uid}')
        return edap_divisions_schema.load(divisions_raw).data

    def add_to_division(self, division_machine_name):
        """ Add user to franchise """
        self.edap.make_uid_member_of_division(self.uid, division_machine_name)

    def remove_from_division(self, division_machine_name):
        """ Remove user from division """
        self.edap.remove_uid_member_of_division(self.uid, division_machine_name)

    def get_teams(self):
        from .serializers import edap_teams_schema
        teams_raw = self.edap.get_teams(f'memberUid={self.uid}')
        return edap_teams_schema.load(teams_raw).data


class Franchise:

    GROUP_FOLDER = 'Franchises'

    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name

    @staticmethod
    def create_folder(folder_name):
        """
        Create subfolder in 'Franchises' folder with read-write access to members of Franchise
        and read access for 'Everybody' team
        """
        nxc = get_nextcloud()
        main_franchises_folder = get_group_folder(Franchise.GROUP_FOLDER)

        if not main_franchises_folder:
            LdapFranchise.create_main_folder()

        create_folder_res = nxc.create_group_folder("/".join([Franchise.GROUP_FOLDER, folder_name]))
        grant_access_res = nxc.grant_access_to_group_folder(create_folder_res.data['id'], folder_name)
        grant_everybody_access = nxc.grant_access_to_group_folder(create_folder_res.data['id'],
                                                                  LdapTeam.EVERYBODY_MACHINE_NAME)
        return create_folder_res.is_ok and grant_access_res.is_ok and grant_everybody_access.is_ok

    @staticmethod
    def create_main_folder():
        """ Create main 'Franchises' folder in root directory with read rights for 'Everybody' team """
        nxc = get_nextcloud()
        create_main_folder_res = nxc.create_group_folder(Franchise.GROUP_FOLDER)
        main_folder_id = create_main_folder_res.data['id']
        nxc.grant_access_to_group_folder(main_folder_id, LdapTeam.EVERYBODY_MACHINE_NAME)
        nxc.set_permissions_to_group_folder(main_folder_id,
                                            LdapTeam.EVERYBODY_MACHINE_NAME,
                                            str(NxcPermission.READ.value))


class LdapFranchise(EdapMixin, Franchise):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapFranchise, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapFranchise(fqdn={self.fqdn})>'

    def create(self):
        """ Create franchise with self.machine_name, self.display_name, create corresponding teams """
        if LdapFranchise.check_exists_by_display_name(self.display_name):
            raise ConstraintError('Franchise with such display name already exists')
        self.edap.create_franchise(machine_name=self.machine_name, display_name=self.display_name)
        # TODO: better move to celery, because takes time
        self.create_teams()

    def create_teams(self):
        """
        When a new franchise is created, an LDAP entry is created for it, and team entries are created as well,
        so there are teams for every <new franchise>-<division> combination.

        Should be called when new Franchise is created
        """
        from .serializers import edap_divisions_schema
        divisions = edap_divisions_schema.load(self.edap.get_divisions()).data
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


class Division:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapDivision(EdapMixin, Division):
    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapDivision, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapDivision(fqdn={self.fqdn}>'

    def create(self):
        """ Create division with self.machine_name, self.display_name, create corresponding teams """
        self.edap.create_division(self.machine_name, display_name=self.display_name)
        # TODO: better move to celery, because takes time
        self.create_teams()

    def create_teams(self):
        """
         When a new division is created, an LDAP entry is created for it, and team entries are created as well,
         so there are teams for every <franchise>-<new division> combination.

         Should be called when new Franchise is created
         """
        from .serializers import edap_franchises_schema
        franchises = edap_franchises_schema.load(self.edap.get_franchises()).data
        for franchise in franchises:
            machine_name = self.edap.make_team_machine_name(franchise.machine_name, self.machine_name)
            display_name = self.edap.make_team_display_name(franchise.display_name, self.display_name)
            self.edap.create_team(machine_name, display_name)


class Team:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapTeam(EdapMixin, Team):

    EVERYBODY_MACHINE_NAME = 'everybody'
    EVERYBODY_DISPLAY_NAME = 'Everybody'

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapTeam, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapTeam(fqdn={self.fqdn}>'

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
        return edap_team_schema.load(everybody_team).data

