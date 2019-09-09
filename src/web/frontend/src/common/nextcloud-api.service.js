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

export default { NxcGroupsService }
