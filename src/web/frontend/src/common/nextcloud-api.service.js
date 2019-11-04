import ApiService from './api.service'

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
  }

}

export default { NxcGroupsService }
