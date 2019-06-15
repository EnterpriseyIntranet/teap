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

export const LdapFranchisesService = {
  get () {
    return ApiService.get(`${BASE_URL}franchises`)
  },

  post (params) {
    return ApiService.post(`${BASE_URL}franchises`, params)
  }
}

export const LdapFranchiseFolderService = {
  post (franchiseMachineName) {
    return ApiService.post(`${BASE_URL}franchises/${franchiseMachineName}/folders`)
  }
}
