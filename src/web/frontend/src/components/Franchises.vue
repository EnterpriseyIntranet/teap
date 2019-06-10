<template>
  <div>
    <h2>Franchises: </h2>
    <!-- Users list -->
    <div>
      <p>Franchises:</p>
      <ul v-if="franchises">
        <li v-for="franchise in franchises" :key="franchise.fqdn">
          <p>{{ franchise }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { LdapFranchisesService } from '../common/ldap-api.service.js'

export default {
  data () {
    return {
      franchises: []
    }
  },

  methods: {
    getFranchises () {
      LdapFranchisesService.get().then((res) => {
        this.franchises = res.data
      })
    },

    deleteFranchise (franchiseName) {
      LdapFranchisesService.delete(franchiseName).then(res => {
        this.$notifier.success({text: 'Franchise successfully deleted'})
        this.getFranchises()
      }).catch(error => {
        this.$notifier.error({title: 'Franchise deleting failed', text: error.response.data.message})
      })
    }

  },
  created () {
    this.getFranchises()
  }
}
</script>
