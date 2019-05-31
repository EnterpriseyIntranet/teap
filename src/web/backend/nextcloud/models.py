""" Models to work with ldap objects, operated by EDAP library """


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
