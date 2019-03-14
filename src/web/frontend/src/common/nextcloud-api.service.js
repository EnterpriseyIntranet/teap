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
  post (username, groupName, action = '') {
    let resource = action ? `users/${username}/groups/subadmins` : `users/${username}/groups`
    return ApiService.post(resource, {'group_name': groupName})
  },

  delete (username, groupName) {
    return ApiService.delete(`users/${username}/groups`, groupName)
  }
}

export const NxcGroupsService = {
  get (slug, action = '') {
    slug = action ? `${slug}/${action}` : slug
    return ApiService.get('groups', slug)
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
  }

}

export default { NxcUsersService, NxcGroupsService, NxcUserGroupsService }
