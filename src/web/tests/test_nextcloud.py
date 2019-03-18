import pytest

from unittest.mock import patch, MagicMock


@pytest.fixture(scope='function')
def nextcloud_mock():
    mock = MagicMock()
    with patch('backend.nextcloud.api.NextCloudMixin.nextcloud', mock) as nextcloud_mock:
        yield nextcloud_mock


@pytest.fixture(scope='function', autouse=True)
def nxc_response_mock():
    mock = MagicMock(return_value="{}")
    with patch('backend.nextcloud.api.NextCloudMixin.nxc_response', mock) as nxc_response:
        yield nxc_response


class TestNextCloudUserApi:

    def test_list_users(self, client, nextcloud_mock, nxc_response_mock):
        client.get('/api/users/')
        # asserts
        assert nxc_response_mock.assert_called_once
        nextcloud_mock.get_users.assert_called_once_with()

    def test_get_user(self, client, nextcloud_mock, nxc_response_mock):
        client.get('/api/users/admin')
        # asserts
        nextcloud_mock.get_user.assert_called_once_with('admin')
        assert nxc_response_mock.assert_called_once

    def test_add_user(self, client, nextcloud_mock):
        username = 'admin'
        password = 'admin'
        res = client.post('/api/users/', json={'username': username, 'password': password})
        # asserts
        assert res.status_code == 201
        nextcloud_mock.add_user.assert_called_once_with(username, password)

    def test_delete_user(self, client, nextcloud_mock):
        client.delete('/api/users/admin')
        # asserts
        nextcloud_mock.delete_user.assert_called_once_with('admin')

        # delete without username
        res = client.delete('/api/users/')
        assert res.status_code == 405

    def test_patch_user(self, client, nextcloud_mock):
        param = 'email'
        value = 'test@test.test'
        client.patch('/api/users/admin', json={'param': param, 'value': value})
        # asserts
        nextcloud_mock.edit_user.assert_called_once_with('admin', param, value)

    def test_enable_disable_user(self, client, nextcloud_mock):
        # enable user
        client.patch('/api/users/admin/enable')
        # asserts
        nextcloud_mock.enable_user.assert_called_once_with('admin')

        # disable user
        client.patch('/api/users/admin/disable')
        # asserts
        nextcloud_mock.disable_user.assert_called_once_with('admin')


class TestNextCloudUserGroupsApi:

    def test_add_to_group(self, client, nextcloud_mock):
        res = client.post('/api/users/admin/groups/', json={'group_name': 'blah'})

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('blah')
        nextcloud_mock.add_to_group.assert_called_once_with('admin', 'blah')
        assert res.status_code == 200

    def test_add_to_unreal_group(self, client, nextcloud_mock):
        nextcloud_mock.get_group = MagicMock(return_value=MagicMock(is_ok=False))
        res = client.post('/api/users/admin/groups/', json={'group_name': 'blah'})

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('blah')
        assert not nextcloud_mock.add_to_group.called
        assert res.status_code == 404

    def test_remove_from_group(self, client, nextcloud_mock):
        res = client.delete('/api/users/admin/groups/blah')

        # asserts
        nextcloud_mock.remove_from_group.assert_called_once_with('admin', 'blah')
        assert res.status_code == 200


class TestNextCloudGroupsApi:

    def test_list_users(self, client, nextcloud_mock, nxc_response_mock):
        client.get('/api/groups/')
        # asserts
        assert nxc_response_mock.assert_called_once
        nextcloud_mock.get_groups.assert_called_once_with()

    def test_get_group(self, client, nextcloud_mock, nxc_response_mock):
        res = client.get('/api/groups/groupname')
        # asserts
        assert res.status_code == 200
        nextcloud_mock.get_group.assert_called_once_with('groupname')
        assert nxc_response_mock.assert_called_once

    def test_add_group(self, client, nextcloud_mock):
        group_name = "new_group"
        res = client.post('/api/groups/', json={"group_name": group_name})
        # asserts
        assert res.status_code == 201
        nextcloud_mock.add_group.assert_called_once_with(group_name)

    def test_delete_user(self, client, nextcloud_mock):
        res = client.delete('/api/groups/groupname')
        # asserts
        assert res.status_code == 202
        nextcloud_mock.delete_group.assert_called_once_with('groupname')

        # delete without username
        res = client.delete('/api/groups/')
        assert res.status_code == 405

    def test_get_group_subadmins(self, client, nextcloud_mock):
        res = client.get('/api/groups/groupname/subadmins')

        # asserts
        assert res.status_code == 200
        nextcloud_mock.get_subadmins.assert_called_once_with('groupname')

    def test_add_subadmin_to_unreal_group(self, client, nextcloud_mock):
        nextcloud_mock.get_group = MagicMock(return_value=MagicMock(is_ok=False))
        res = client.post('/api/groups/qwe/subadmins', json={'username': 'admin'})

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('qwe')
        assert not nextcloud_mock.add_to_group.called
        assert not nextcloud_mock.create_subadmin.called
        assert res.status_code == 404

    def test_add_subadmin_to_group(self, client, nextcloud_mock):
        res = client.post('/api/groups/asd/subadmins', json={'username': 'admin'})

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('asd')
        nextcloud_mock.create_subadmin.assert_called_once_with('admin', 'asd')
        assert res.status_code == 201

    def test_delete_subadmin_from_unreal_group(self, client, nextcloud_mock):
        nextcloud_mock.get_group = MagicMock(return_value=MagicMock(is_ok=False))
        res = client.delete('/api/groups/qwe/subadmins/admin')

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('qwe')
        assert not nextcloud_mock.add_to_group.called
        assert not nextcloud_mock.remove_subadmin.called
        assert res.status_code == 404

    def test_delete_subadmin_from_group(self, client, nextcloud_mock):
        res = client.delete('/api/groups/asd/subadmins/admin')

        # asserts
        nextcloud_mock.get_group.assert_called_once_with('asd')
        nextcloud_mock.remove_subadmin.assert_called_once_with('admin', 'asd')
        assert res.status_code == 201