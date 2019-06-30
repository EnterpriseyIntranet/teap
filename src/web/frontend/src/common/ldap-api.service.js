import ApiService from './api.service'

const BASE_URL = 'ldap/'

export const LdapConfigDivisionsService = {
  get () {
    return ApiService.get(`${BASE_URL}config-divisions`)
  },

  post (params) {
    return ApiService.post(`${BASE_URL}config-divisions`, params)
  }
}

export const LdapDivisionsService = {
  get (params) {
    return ApiService.get(`${BASE_URL}divisions`, '', params)
  }
}

export const LdapDivisionService = {
  delete (divisionName) {
    return ApiService.delete(`${BASE_URL}divisions`, divisionName)
  }
}

export const LdapFranchisesService = {
  get (params) {
    return ApiService.get(`${BASE_URL}franchises`, '', params)
  },

  post (params) {
    return ApiService.post(`${BASE_URL}franchises`, params)
  }
}

export const LdapFranchiseService = {
  getSuggestedName (franchiseMachineName) {
    return ApiService.get(`${BASE_URL}franchises/${franchiseMachineName}/suggested-name`)
  }
}

export const LdapFranchiseFolderService = {
  post (franchiseMachineName) {
    return ApiService.post(`${BASE_URL}franchises/${franchiseMachineName}/folders`)
  }
}

export const LdapTeamsService = {
  get (params) {
    return ApiService.get(`${BASE_URL}teams`, '', params)
  }
}

export const LdapUserFranchisesService = {
  post (uid, params) {
    return ApiService.post(`${BASE_URL}user/${uid}/franchises`, params)
  },

  delete (uid, params) {
    return ApiService.delete(`${BASE_URL}user/${uid}/franchises`, '', params)
  }
}

export const LdapUserDivisionsService = {
  post (uid, params) {
    return ApiService.post(`${BASE_URL}user/${uid}/divisions`, params)
  },

  delete (uid, params) {
    return ApiService.delete(`${BASE_URL}user/${uid}/divisions`, '', params)
  }
}

export const LdapUserTeamsService = {
  post (uid, params) {
    return ApiService.post(`${BASE_URL}user/${uid}/teams`, params)
  },

  delete (uid, params) {
    return ApiService.delete(`${BASE_URL}user/${uid}/teams`, '', params)
  }
}
