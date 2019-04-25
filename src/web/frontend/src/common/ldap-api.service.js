import ApiService from './api.service'

const BASE_URL = 'ldap/'

export const LdapDivisionsService = {
  get () {
    return ApiService.get(`${BASE_URL}divisions`)
  },

  post (params) {
    return ApiService.post(`${BASE_URL}divisions`, params)
  },

  delete (divisionName) {
    return ApiService.delete(`ldap/divisions`, divisionName)
  }
}
