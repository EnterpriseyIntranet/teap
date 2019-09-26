import ApiService from './api.service'

const BASE_URL = 'actions'

export const ActionsService = {

  get (params) {
    return ApiService.get(`${BASE_URL}`, '', params)
  },

  post (id) {
    return ApiService.post(`${BASE_URL}/${id}`)
  }
}
