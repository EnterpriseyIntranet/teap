""" Models to work with ldap objects, operated by EDAP library """
from .utils import get_edap


class User:
    def __init__(self, uid, given_name, mail, surname):
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname

    def delete_user(self, *args, **kwargs):
        pass

    def add_user_to_group(self, *args, **kwargs):
        pass


class LdapUser(User):

    def __init__(self, fqdn, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapUser, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapUser(fqdn={self.fqdn}, uid={self.uid})>'


class Franchise:
    def __init__(self, machine_name=None, display_name=None):
        self.machine_name = machine_name
        self.display_name = display_name


class LdapFranchise(Franchise):
    def __init__(self, fqdn, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapFranchise, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapFranchise(fqdn={self.fqdn}>'

    def create_teams(self):
        """
        When a new country is created, an LDAP entry is created for it, and team entries are created as well,
        so there are teams for every <new country>-<division> combination.
        """
        from .serializers import edap_divisions_schema
        edap = get_edap()
        divisions = edap_divisions_schema.load(edap.get_divisions()).data
        for division in divisions:
            machine_name = "{}-{}".format(self.machine_name, division.machine_name)
            display_name = "{}-{}".format(self.display_name, division.display_name)
            edap.create_division(machine_name, display_name)


class Division:
    def __init__(self, fqdn, machine_name=None, display_name=None):
        super(Division, self).__init__(fqdn)
        self.machine_name = machine_name
        self.display_name = display_name


class LdapDivision(Division):
    def __init__(self, fqdn, *args, **kwargs):
        self.fqdn = fqdn
        super(LdapDivision, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<LdapDivision(fqdn={self.fqdn}>'

