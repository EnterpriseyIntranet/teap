<template>
  <div>
    <!-- Create franchise -->
    <div>
      <p>New franchise: </p>
      <p>
        <label>country:</label>
        <input type="text" v-model="franchiseCode">
      </p>

      <!-- TODO: add select for country instead of input -->

      <button @click.prevent="createFranchise()">Submit</button>
    </div>
  </div>
</template>

<script>
import { LdapFranchisesService } from '@/common/ldap-api.service.js'

export default {

  data () {
    return {
      franchiseCode: null
    }
  },
  methods: {

    createFranchise () {
      // TODO: create all divisions for country, create chat
      LdapFranchisesService.post({franchise_code: this.franchiseCode})
        .then(response => {
          this.franchiseCode = null
          this.$notifier.success({text: response.data.message})
        })
        .catch(error => {
          this.$notifier.error({text: error.response.data.message})
        })
    }

  }
}
</script>
