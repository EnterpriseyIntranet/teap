import time

from flask import Blueprint, jsonify, request
from flask.views import MethodView
from ..edap import ObjectDoesNotExist, ConstraintError, MultipleObjectsFound
from marshmallow import ValidationError

from .. import utils
from .serializers import edap_user_schema, edap_users_schema, edap_franchise_schema, edap_franchises_schema, \
    edap_divisions_schema, edap_teams_schema, edap_division_schema
from .api_serializers import api_franchise_schema, api_user_schema, api_users_schema, api_franchises_schema, \
    api_divisions_schema, api_teams_schema

from .models import LdapDivision, LdapFranchise, LdapUser
from .utils import get_config_divisions, merge_divisions, EdapMixin, send_password_reset_email, get_edap, verify_reset_password_token, PWResetEligibilityExc

blueprint = Blueprint('divisions_api', __name__, url_prefix='/api/ldap/')
blueprint.json_encoder = utils.EncoderWithBytes


@blueprint.errorhandler(ObjectDoesNotExist)
def handle_not_found(e):
    return jsonify({'message': str(e)}), 404


class UserListViewSet(EdapMixin, MethodView):

    def get(self):
        """ List users """
        res = self.edap.get_users()
        data = edap_users_schema.load(res)
        return jsonify(api_users_schema.dump(data))

    @utils.authorize_only_hr_admins()
    def post(self):
        """ Create user """

        try:
            user_data = api_user_schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        password = user_data.pop('password')
        user = LdapUser(**user_data)
        try:
            res = user.create(password=password)
        except Exception as e:
            return jsonify({'message': "Failed to create user. {}".format(e)}), 400

        return jsonify(res)


class UserAdministrationViewSet(EdapMixin,
                                MethodView):
    @utils.authorize_only_hr_admins()
    def get(self):
        # Render a form to send email

        return flask.render_template(
                "templates/send_reset.html",
                details_form=SendResetEmailForm())

    @utils.authorize_only_hr_admins()
    def post(self):
        # Send reset email
        form = SendResetEmailForm()
        if not form.validate_on_submit():
            return
        recovery_email = form.email.data
        username = form.username.data
        now = time.time()
        try:
            user = edap_user_schema.load(self.edap.get_user(username))
        except MultipleObjectsFound:
            return jsonify({'message': 'More than 1 user found'}), 409
        except ObjectDoesNotExist:
            return jsonify({'message': f'User {username} does not exist'}), 404

        data = dict(
                username=username,
                now=now,
                )
        send_password_reset_email(to=recovery_email, data=data)
        flask.flash("Sent password recovery email")
        return flask.redirect(flask.url_for("divisions_api.admin_api"))


class UserRetrieveViewSet(EdapMixin,
                          MethodView):
    """ ViewSet for single user """
    def get(self, username):
        """ List users """
        try:
            user = edap_user_schema.load(self.edap.get_user(username))
        except MultipleObjectsFound:
            return jsonify({'message': 'More than 1 user found'}), 409
        except ObjectDoesNotExist:
            return jsonify({'message': 'User does not exist'}), 404

        auth_err = utils.auth_err_if_user_other_than(username) and utils.auth_err_if_user_not_hr_admin()
        if auth_err:
            return auth_err

        user_groups = self.edap.get_user_groups(username)
        user = {
            **api_user_schema.dump(user),
            "groups": [group for group in user_groups],
            "franchises": api_franchises_schema.dump(user.get_franchises()),
            "divisions": api_divisions_schema.dump(user.get_divisions()),
            "teams": api_teams_schema.dump(user.get_teams())
        }
        return jsonify(user)

    def post(self, username):
        auth_err = utils.auth_err_if_user_other_than(username) and utils.auth_err_if_user_not_hr_admin()
        if auth_err:
            return auth_err

        form = UserForm()

        if not form.validate_on_submit():
            all_errors = []
            for errors in form.errors.values():
                all_errors.extend(errors)
            all_errors_str = ", ".join(all_errors)
            msg = f"Form validation error: {all_errors_str}"
            flask.flash(msg)

            return flask.redirect(flask.url_for("divisions_api.details_change"))

        form_dict = request.form

        current_password = form_dict.get("password")
        user = LdapUser.get_from_edap(username)

        if not user.check_password(current_password):
            msg = "Password mismatch, specify your current password to make any changes."
            flask.flash(msg)
            return flask.redirect(flask.url_for("divisions_api.details_change"))

        if form_dict.get("new_password"):
            try:
                user.modify_password(form_dict["new_password"])
            except Exception as exc:
                msg = flask.Markup(f"Couldn't change password: {str(exc)}")
                flask.flash(msg)

        if form.avatar.data:
            user.modify("picture_bytes", form.avatar.data)

        specified_data = set(form_dict.keys())
        modifiable_data = {
            "name",
            "surname",
        }
        for key in modifiable_data.intersection(specified_data):
            if not (value := form_dict.get(key)):
                continue

            msg = f"Changed {key} to {value}"
            flask.flash(msg)

            user.modify(key, value)
        return flask.redirect(flask.url_for("divisions_api.details_change"))

    @utils.authorize_only_hr_admins()
    def delete(self, username):
        """ Delete user """
        result = dict(success=True)
        try:
            user = edap_user_schema.load(self.edap.get_user(username))
            user.delete()
        except Exception as exc:
            result['success'] = False
            result['message'] = str(exc)
            return jsonify(result), 500
        return jsonify(result)


class UserGroupViewSet(EdapMixin,
                       MethodView):

    @utils.authorize_only_hr_admins()
    def post(self, username):
        """ Add user to group """
        group_fqdn = request.json.get('fqdn')
        if not group_fqdn:
            return jsonify({'message': 'fqdn is required parameter'}), 400
        try:
            self.edap.make_uid_member_of(username, group_fqdn)
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 404
        return jsonify({'message': 'Success'}), 200

    @utils.authorize_only_hr_admins()
    def delete(self, username):
        """ Remove user from group """
        group_fqdn = request.json.get('fqdn')
        if not group_fqdn:
            return jsonify({'message': 'fqdn is a required parameter'})
        try:
            self.edap.remove_uid_member_of(username, group_fqdn)
        except ConstraintError as e:
            return jsonify({'message': f'Failed to delete. {e}'}), 400
        return jsonify({'message': 'Success'}), 202


class ConfigDivisionsListViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get merged divisions from config and ldap """
        ldap_divisions = self.edap.get_divisions()
        config_divisions = get_config_divisions()
        divisions = merge_divisions(config_divisions, ldap_divisions)
        return jsonify({'divisions': divisions})

    @utils.authorize_only_hr_admins()
    def post(self):
        """ Create division that present in config file, but not in ldap """
        div_machine_name = request.json.get('machine_name')
        if not div_machine_name:
            return jsonify({"message": "'machine_name' is required field"}), 400
        config_divisions = get_config_divisions()
        if div_machine_name not in config_divisions:
            return jsonify({"message": "Division doesn't exist in config file"}), 400
        div_display_name = config_divisions[div_machine_name]
        division = LdapDivision(machine_name=div_machine_name, display_name=div_display_name)
        res = division.create()
        return jsonify(res)


class DivisionsViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get divisions from ldap """
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        ldap_divisions = edap_divisions_schema.load(self.edap.get_divisions(search))
        return jsonify(api_divisions_schema.dump(ldap_divisions))


class DivisionViewSet(EdapMixin, MethodView):

    @utils.authorize_only_hr_admins()
    def delete(self, division_name):
        self.edap.delete_division(division_name)
        return jsonify({'message': 'Deleted'}), 202


class FranchisesViewSet(EdapMixin, MethodView):

    def get(self):
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        franchises = edap_franchises_schema.load(self.edap.get_franchises(search))
        return jsonify(api_franchises_schema.dump(franchises))

    @utils.authorize_only_hr_admins()
    def post(self):
        franchise = api_franchise_schema.load(request.json)
        try:
            create_res = franchise.create()
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 409
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        return jsonify(create_res), 201


def suggest_franchise_name(franchise_machine_name):
    try:
        suggested_name = LdapFranchise.suggest_name(franchise_machine_name)
    except KeyError:
        return jsonify({'message': 'Unknown country code'}), 400
    return jsonify({'data': suggested_name})


class FranchiseFoldersViewSet(EdapMixin, MethodView):

    @utils.authorize_only_hr_admins()
    def post(self, franchise_machine_name):
        franchise = edap_franchise_schema.load(self.edap.get_franchise(franchise_machine_name))
        res = franchise.create_folder(franchise.display_name)
        return jsonify({'success': res}), 201 if res else 500


class TeamsViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get teams from ldap """
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        ldap_teams = edap_teams_schema.load(self.edap.get_teams(search))
        return jsonify(api_teams_schema.dump(ldap_teams))


class TeamViewSet(EdapMixin, MethodView):

    @utils.authorize_only_hr_admins()
    def delete(self, machine_name):
        """ Delete single team """
        self.edap.delete_team(machine_name)
        return jsonify({'message': 'success'}), 202


class UserFranchisesViewSet(EdapMixin, MethodView):

    @utils.authorize_only_hr_admins()
    def post(self, uid):
        """ add user to franchise """
        user = edap_user_schema.load(self.edap.get_user(uid))  # to check if user exists, or return 404
        machine_name = request.json.get('machineName')
        franchise = edap_franchise_schema.load(self.edap.get_franchise(machine_name))
        franchise.add_user(uid)
        return jsonify({'message': 'success'}), 200

    @utils.authorize_only_hr_admins()
    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid))
        machine_name = request.json.get('machineName')
        user.remove_from_franchise(machine_name)
        return jsonify({'message': 'success'}), 202


class UserDivisionsViewSet(EdapMixin, MethodView):

    @utils.authorize_only_hr_admins()
    def post(self, uid):
        """ add user to team """
        user = edap_user_schema.load(self.edap.get_user(uid))  # to check if user exists, or return 404
        machine_name = request.json.get('machineName')
        division = edap_division_schema.load(self.edap.get_division(machine_name))
        division.add_user(uid)
        return jsonify({'message': 'success'}), 200

    @utils.authorize_only_hr_admins()
    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid))
        machine_name = request.json.get('machineName')
        user.remove_from_division(machine_name)
        return jsonify({'message': 'success'}), 202


class UserTeamsViewSet(EdapMixin, MethodView):

    def post(self, uid):
        """ add user to team """
        user = edap_user_schema.load(self.edap.get_user(uid))
        machine_name = request.json.get('machineName')
        user.add_to_team(machine_name)
        return jsonify({'message': 'success'}), 200

    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid))
        machine_name = request.json.get('machineName')
        user.remove_from_team(machine_name)
        return jsonify({'message': 'success'}), 202


def handle_reset(username, token, new_password):
    try:
        user = LdapUser.get_from_edap(username)
    except MultipleObjectsFound:
        raise ValueError(f'More than 1 user(s) {username} found')
    except ObjectDoesNotExist:
        raise ValueError(f'User {username} does not exist')

    if uid := flask_login.current_user.get_id():
        if uid != username:
            raise ValueError(f"You are logged in as '{uid}', which is an another user than '{username}'.")

    try:
        if not verify_reset_password_token(token, username):
            raise ValueError("The request is weird.")
    except PWResetEligibilityExc as exc:
        msg = f"There was a problem with the reset request: {str(exc)}"
        raise ValueError(msg)

    user.modify_password(new_password)


import io

import flask
import flask_wtf
import flask_wtf.file
import flask_login
import wtforms
import PIL.Image


def convert_image_bytes_to_jpeg(some_bytes, max_size=128):
    if not some_bytes:
        return some_bytes
    in_buf = io.BytesIO()
    in_buf.write(some_bytes.read())

    img = PIL.Image.open(in_buf)
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), PIL.Image.ANTIALIAS)

    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    img_bytes = buf.getvalue()
    return img_bytes


class SendResetEmailForm(flask_wtf.FlaskForm):
    username = wtforms.StringField(
            "Target's Username")
    email = wtforms.StringField(
            "Target's email")
            # "Target's email", [wtforms.validators.Email("You have to provide a valid e-mail address")])


class UserForm(flask_wtf.FlaskForm):
    name = wtforms.StringField(
            "Your Name")
    surname = wtforms.StringField(
            "Your Surname")
    new_password = wtforms.PasswordField(
            "Your new password",
            [wtforms.validators.EqualTo('new_password_confirm', message='Passwords must match')])
    new_password_confirm = wtforms.PasswordField(
            "Your new password (confirm)")
    avatar = flask_wtf.file.FileField(
            "Your new avatar", filters=[convert_image_bytes_to_jpeg])
    password = wtforms.PasswordField(
            "Your current password", [wtforms.validators.DataRequired("You need to specify password to change settings")])


@blueprint.route("/me", methods=["GET"])
def details_change():
    form = UserForm()
    edap = get_edap()
    try:
        uid = flask_login.current_user.id
    except AttributeError:
        return flask.redirect(flask.url_for(f"login", next=flask.url_for("divisions_api.details_change")))

    user = LdapUser.get_from_edap(uid)

    form.name.data = user.given_name
    form.surname.data = user.surname

    return flask.render_template(
            "templates/me.html",
            user=user,
            details_form=form,
            bp_prefix=blueprint.url_prefix)


user_list_view = UserListViewSet.as_view('users_api')
blueprint.add_url_rule('/users/', view_func=user_list_view, methods=['GET', 'POST'])

user_view = UserRetrieveViewSet.as_view('user_api')
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['GET', 'DELETE'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['POST'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['PATCH'])
blueprint.add_url_rule('/users/<username>/<action>', view_func=user_view, methods=['PATCH'])

user_admin = UserAdministrationViewSet.as_view('admin_api')
blueprint.add_url_rule('/send_reset_pw', view_func=user_admin, methods=['POST'])
blueprint.add_url_rule('/send_reset_pw', view_func=user_admin, methods=['GET'])

user_group_view = UserGroupViewSet.as_view('user_groups_api')
blueprint.add_url_rule('/users/<username>/groups/', view_func=user_group_view, methods=['POST', 'DELETE'])

config_divisions_list_view = ConfigDivisionsListViewSet.as_view('config_divisions_api')
blueprint.add_url_rule('config-divisions', view_func=config_divisions_list_view, methods=['GET', 'POST'])

divisions_list_view = DivisionsViewSet.as_view('divisions_api')
blueprint.add_url_rule('divisions', view_func=divisions_list_view, methods=['GET'])

division_view = DivisionViewSet.as_view('division_api')
blueprint.add_url_rule('divisions/<division_name>', view_func=division_view, methods=['DELETE'])

franchises_view = FranchisesViewSet.as_view('franchise_api')
blueprint.add_url_rule('franchises', view_func=franchises_view, methods=['GET', 'POST'])

blueprint.add_url_rule('franchises/<franchise_machine_name>/suggested-name',
                       view_func=suggest_franchise_name,
                       methods=['GET'])

franchise_folders_view = FranchiseFoldersViewSet.as_view('franchise_folders_api')
blueprint.add_url_rule('franchises/<franchise_machine_name>/folders', view_func=franchise_folders_view, methods=['POST'])

teams_view = TeamsViewSet.as_view('teams_api')
blueprint.add_url_rule('teams', view_func=teams_view, methods=['GET'])

team_view = TeamViewSet.as_view('team_api')
blueprint.add_url_rule('teams/<machine_name>', view_func=team_view, methods=['DELETE'])

user_franchises_view = UserFranchisesViewSet.as_view('user_franchises_api')
blueprint.add_url_rule('user/<uid>/franchises', view_func=user_franchises_view, methods=['POST', 'DELETE'])

user_divisions_view = UserDivisionsViewSet.as_view('user_divisions_api')
blueprint.add_url_rule('user/<uid>/divisions', view_func=user_divisions_view, methods=['POST', 'DELETE'])

user_teams_view = UserTeamsViewSet.as_view('user_teams_api')
blueprint.add_url_rule('user/<uid>/teams', view_func=user_teams_view, methods=['POST', 'DELETE'])
