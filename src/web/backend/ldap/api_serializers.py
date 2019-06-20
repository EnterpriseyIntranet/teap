"""
Serializers to process data from .models instances to json and backwards to transfer data via REST api
"""
from marshmallow import Schema, fields, post_load

from .models import LdapUser, LdapFranchise


class ApiUserSchema(Schema):
    """ Serialize .models.LdapUser instances to json and backwards """
    uid = fields.Str()
    given_name = fields.Str()
    mail = fields.Str()
    surname = fields.Str()

    @post_load
    def make_user(self, data):
        return LdapUser(**data)


class ApiFranchiseSchema(Schema):
    """ Serialize .models.LdapFranchise instances to json and backwards """
    machine_name = fields.Str(dump_to='machineName', load_from='machineName')
    display_name = fields.Str(dump_to='displayName', load_from='displayName')

    @post_load
    def make_franchise(self, data):
        return LdapFranchise(**data)


api_user_schema = ApiUserSchema()
api_users_schema = ApiUserSchema(many=True)

api_franchise_schema = ApiFranchiseSchema()
api_franchises_schema = ApiFranchiseSchema(many=True)
