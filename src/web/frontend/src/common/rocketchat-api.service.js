import ApiService from './api.service'

const BASE_URL = 'rocket/'

export const RocketChannelsService = {

  post (params) {
    return ApiService.post(`${BASE_URL}channels`, params)
  }
}

export const RocketUsersService = {

  post (params) {
    return ApiService.post(`${BASE_URL}users`, params)
  }
}

export const RocketUserChannelsService = {
  post (uid, channel) {
    return ApiService.post(`${BASE_URL}users/${uid}/channels`, {channel: channel})
  },

  delete (uid, groupId) {
    return ApiService.delete(`${BASE_URL}users/${uid}/channels/${groupId}`)
  },

  addToTeamChats (uid, teamMachineName) {
    return ApiService.post(`${BASE_URL}users/${uid}/teams/${teamMachineName}/chats`)
  }
}
