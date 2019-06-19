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
