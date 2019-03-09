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
  post (username, groupName) {
    return ApiService.post(`users/${username}/groups`, {'group_name': groupName})
  },

  delete (username, groupName) {
    return ApiService.delete(`users/${username}/groups`, groupName)
  }
}

export const NxcGroupsService = {
  get (slug) {
    return ApiService.get('groups', slug)
  },

  post (params) {
    return ApiService.post('groups', params)
  },

  delete (slug) {
    return ApiService.delete('groups', slug)
  }
}

export default { NxcUsersService, NxcGroupsService, NxcUserGroupsService }
