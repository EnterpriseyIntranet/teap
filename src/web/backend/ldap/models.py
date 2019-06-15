""" Models to work with ldap objects, operated by EDAP library """
from edap import ObjectDoesNotExist

from .utils import get_edap

# TODO: separate layer with edap from data models


class User:
    def __init__(self, uid, given_name, mail=None, surname=None, groups=None):
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname
        self.groups = groups

    def delete_user(self, *args, **kwargs):
        pass

    def add_user_to_group(self, *args, **kwargs):
        pass


class LdapUser(User):

    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapUser, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapUser(fqdn={self.fqdn}, uid={self.uid})>'

    def create(self, password):
        edap = get_edap()
        edap.add_user(self.uid, self.given_name, self.surname, password)

        for group in self.groups:
            edap.make_uid_member_of(self.uid, group)

        # add user to 'Everybody' team
        everybody_team = LdapTeam.get_everybody_team()
        edap.make_user_member_of_team(self.uid, everybody_team.machine_name)

    def get_teams(self):
        """ Get teams where user is a member """
        from .serializers import edap_teams_schema
        edap = get_edap()
        user_teams = edap.get_teams(f'memberUid={self.uid}')
        return edap_teams_schema.load(user_teams).data

    def add_to_team(self, team_machine_name):
        """ Add user to team and to respective franchise and division groups """
        # TODO: add to rocket channel
        from .serializers import edap_franchise_schema, edap_division_schema
        edap = get_edap()
        edap.make_user_member_of_team(self.uid, team_machine_name)
        franchise, division = edap.get_team_component_units(team_machine_name)
        franchise = edap_franchise_schema.load(franchise).data
        division = edap_division_schema.load(division).data
        edap.make_user_member_of_franchise(self.uid, franchise.machine_name)
        edap.make_uid_member_of_division(self.uid, division.machine_name)


class Franchise:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapFranchise(Franchise):
    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapFranchise, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapFranchise(fqdn={self.fqdn}>'

    def create(self):
        """ Create franchise with self.machine_name, self.display_name, create corresponding teams """
        edap = get_edap()
        edap.create_franchise(self.machine_name)
        self.display_name = edap.label_franchise(self.machine_name).encode("UTF-8")
        # TODO: better move to celery, because takes time
        self.create_teams()
        # TODO: create folder, with read rights for 'everybody' team, read-write for members of a country

    def create_teams(self):
        """
        When a new franchise is created, an LDAP entry is created for it, and team entries are created as well,
        so there are teams for every <new franchise>-<division> combination.

        Should be called when new Franchise is created
        """
        from .serializers import edap_divisions_schema
        edap = get_edap()
        divisions = edap_divisions_schema.load(edap.get_divisions()).data
        for division in divisions:
            machine_name = edap.make_team_machine_name(self.machine_name, division.machine_name)
            display_name = edap.make_team_display_name(self.display_name, division.display_name)
            edap.create_team(machine_name, display_name)


class Division:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name

    def create(self):
        """ Create division with self.machine_name, self.display_name, create corresponding teams """
        edap = get_edap()
        edap.create_division(self.machine_name, display_name=self.display_name)
        # TODO: better move to celery, because takes time
        self.create_teams()

    def create_teams(self):
        """
         When a new division is created, an LDAP entry is created for it, and team entries are created as well,
         so there are teams for every <franchise>-<new division> combination.

         Should be called when new Franchise is created
         """
        from .serializers import edap_franchises_schema
        edap = get_edap()
        franchises = edap_franchises_schema.load(edap.get_franchises()).data
        for franchise in franchises:
            machine_name = edap.make_team_machine_name(franchise.machine_name, self.machine_name)
            display_name = edap.make_team_display_name(franchise.display_name, self.display_name)
            edap.create_team(machine_name, display_name)


class LdapDivision(Division):
    def __init__(self, fqdn=None, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapDivision, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapDivision(fqdn={self.fqdn}>'


class Team:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapTeam(Team):

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

