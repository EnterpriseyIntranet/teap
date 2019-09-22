"""
Serializers to process data from .models instances to json and backwards to transfer data via REST api
"""
from marshmallow import Schema, fields, post_load

from .models import LdapUser, LdapFranchise, LdapDivision, LdapTeam


class ApiUserSchema(Schema):
    """ Serialize .models.LdapUser instances to json and backwards """
    uid = fields.Str(required=True)
    given_name = fields.Str(data_key='name', required=True)
    mail = fields.Str()
    surname = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)
    groups = fields.List(fields.Str)


class ApiBaseGroupSchema(Schema):
    """ Serialize ldap models for posixGroup to json and backwards """
    fqdn = fields.Str()
    machine_name = fields.Str(data_key='machineName')
    display_name = fields.Str(data_key='displayName')


class ApiFranchiseSchema(ApiBaseGroupSchema):
    """ Serialize .models.LdapFranchise instances to json and backwards """

    @post_load
    def make_franchise(self, data, **kwargs):
        return LdapFranchise(**data)


class ApiDivisionSchema(ApiBaseGroupSchema):
    """ Serialize .models.LdapDivision instances to json and backwards """

    @post_load
    def make_division(self, data, **kwargs):
        return LdapDivision(**data)


class ApiTeamSchema(ApiBaseGroupSchema):
    """ Serialize .models.LdapTeam instances to json and backwards """

    @post_load
    def make_team(self, data, **kwargs):
        return LdapTeam(**data)


api_user_schema = ApiUserSchema()
api_users_schema = ApiUserSchema(many=True)

api_franchise_schema = ApiFranchiseSchema()
api_franchises_schema = ApiFranchiseSchema(many=True)

api_division_schema = ApiDivisionSchema()
api_divisions_schema = ApiDivisionSchema(many=True)

api_team_schema = ApiTeamSchema()
api_teams_schema = ApiTeamSchema(many=True)
