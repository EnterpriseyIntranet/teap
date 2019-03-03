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

export const NxcGroupsService = {
  get (slug, action) {
    return ApiService.get('groups', slug)
  },

  post (params) {
    return ApiService.post('groups', params)
  },

  delete (slug) {
    return ApiService.delete('groups', slug)
  }
}

export default { NxcUsersService, NxcGroupsService }
