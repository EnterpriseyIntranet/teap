import pytest

from unittest.mock import patch, MagicMock


@pytest.fixture(scope='function')
def nextcloud_mock():
    mock = MagicMock()
    with patch('teap.nextcloud.api.NextCloudMixin.nextcloud', mock) as nextcloud_mock:
        yield nextcloud_mock


@pytest.fixture(scope='function', autouse=True)
def nxc_response_mock():
    mock = MagicMock(return_value="{}")
    with patch('teap.nextcloud.api.NextCloudMixin.nxc_response', mock) as nxc_response:
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
        client.post('/api/users/', json={'username': username, 'password': password})
        # asserts
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
