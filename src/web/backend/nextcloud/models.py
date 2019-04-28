""" Models to work with ldap objects, operated by EDAP library """


class BaseLdapModel:

    def __init__(self, fqdn):
        self.fqdn = fqdn


class User(BaseLdapModel):
    """ Edap user model """
    def __init__(self, fqdn, uid, given_name, mail, surname):
        super(BaseLdapModel, self).__init__(fqdn)
        self.uid = uid
        self.given_name = given_name
        self.mail = mail
        self.surname = surname

    def __repr__(self):
        return f'<User(fqdn={self.fqdn}, uid={self.uid})>'

    def delete_user(self, edap, **kwargs):
        pass

    def add_user_to_group(self, edap, **kwargs):
        pass
