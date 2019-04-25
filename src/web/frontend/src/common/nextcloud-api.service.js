import ApiService from './api.service'

export const NxcUsersService = {
  get (slug, action) {
    return ApiService.get('users', slug)
  },

  delete (slug) {
    return ApiService.delete('users', slug)
  },

  post (params) {
    return ApiService.post('users', params)
  }
}

export const NxcUserGroupsService = {
  post (username, groupFqdn, action = '') {
    let resource = action ? `users/${username}/groups/subadmins` : `users/${username}/groups`
    return ApiService.post(resource, {'fqdn': groupFqdn})
  },

  delete (username, fqdn) {
    return ApiService.delete(`users/${username}/groups`, '', {fqdn: fqdn})
  }
}

export const NxcGroupsService = {
  get (slug, action = '', params) {
    slug = action ? `${slug}/${action}` : slug
    return ApiService.get('groups', slug, params)
  },

  post (params) {
    return ApiService.post('groups', params)
  },

  delete (slug) {
    return ApiService.delete('groups', slug)
  },

  createSubadmin (user, group) {
    return ApiService.post(`groups/${group}/subadmins`, {username: user})
  },

  deleteSubadmin (user, group) {
    return ApiService.delete(`groups/${group}/subadmins`, user)
  },

  deleteEmpty (data) {
    data['empty'] = true
    return ApiService.delete('groups', '', data)
  }

}

export const GroupWithFolderService = {
  post (params) {
    return ApiService.post('groups-with-folders', params)
  }
}

export const GroupFolderService = {
  post (params) {
    return ApiService.post('groupfolder', params)
  }
}

export default { NxcUsersService, NxcGroupsService, NxcUserGroupsService }
