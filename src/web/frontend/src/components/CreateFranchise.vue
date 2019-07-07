<template>
  <div>
    <!-- Create franchise -->
    <div>
      <p>New franchise: </p>
      <p>
        <label>Machine name (country code):</label>
        <input type="text" @keyup="getSuggestedName()" v-model="machineName">
        <label>Display name:</label>
        <input type="text" v-model="displayName">
        <button @click.prevent="createFranchise()">Submit</button>
      </p>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'
import { LdapFranchisesService, LdapFranchiseService } from '@/common/ldap-api.service.js'

export default {

  data () {
    return {
      machineName: null,
      displayName: null
    }
  },
  methods: {

    createFranchise () {
      LdapFranchisesService.post({machineName: this.machineName, displayName: this.displayName})
        .then(response => {
          this.$notifier.success({text: response.data.message})
          this.machineName = null
          this.displayName = null

          let channelRes = response.data.rocket
          let folderRes = response.data.folder

          if (!channelRes.success) {
            this.$notifier.error({title: 'Error creating rocket chat channel for franchise', text: channelRes.error})
          }

          if (!folderRes.success) {
            this.$notifier.error({title: 'Error creating group folder for franchise', text: folderRes.error})
          }
        }, (error) => {
          this.$notifier.error({title: 'Error creating franchise', text: error.response.data.message})
        })
    },

    getSuggestedName: _.debounce(function () {
      LdapFranchiseService.getSuggestedName(this.machineName)
        .then(
          response => {
            if (!this.displayName) {
              this.displayName = response.data.data
            }
          },
          error => {
            console.log('Error getting suggested name', error)
          }
        )
    }, 700)

  }
}
</script>
