import ApiService from './api.service'

const BASE_URL = 'ldap/'

export const LdapUsersService = {
  get (slug, action) {
    return ApiService.get(`${BASE_URL}users`, slug)
  },

  delete (slug) {
    return ApiService.delete(`${BASE_URL}users`, slug)
  },

  post (params) {
    return ApiService.post(`${BASE_URL}users`, params)
  }
}

export const LdapUserGroupsService = {
  post (username, groupFqdn, action = '') {
    let resource = action ? `${BASE_URL}users/${username}/groups/subadmins` : `users/${username}/groups`
    return ApiService.post(resource, {'fqdn': groupFqdn})
  },

  delete (username, fqdn) {
    return ApiService.delete(`${BASE_URL}users/${username}/groups`, '', {fqdn: fqdn})
  }
}

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
  },

  delete (machineName) {
    return ApiService.delete(`${BASE_URL}teams/${machineName}`)
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
