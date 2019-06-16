<template>
  <div>
    <!-- Create franchise -->
    <div>
      <p>New franchise: </p>
      <p>
        <label>Machine name (country code):</label>
        <input type="text" v-model="machineName">
        <label>Display name:</label>
        <input type="text" v-model="displayName">
        <button @click.prevent="createFranchise()">Submit</button>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { LdapFranchisesService, LdapFranchiseFolderService } from '@/common/ldap-api.service.js'
import { RocketChannelsService } from '../common/rocketchat-api.service'

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
          let groupFolderReq = LdapFranchiseFolderService.post(this.machineName)
            .catch(error => {
              this.$notifier.error({title: 'Error creating group folder for division', text: error.response.data.message})
            })
          let rocketChannelReq = RocketChannelsService.post({channel_name: `Franchise-${this.displayName}`})
            .catch(error => {
              this.$notifier.error({title: 'Error creating rocket chat channel for division', text: error.response.data.error})
            })
          this.$notifier.success({text: response.data.message})
          this.machineName = null
          this.displayName = null
          return axios.all([groupFolderReq, rocketChannelReq])
        }, (error) => {
          this.$notifier.error({title: 'Error creating division', text: error.response.data.message})
        }).then(axios.spread((folderRes, rocketChannelRes) => {
          if (folderRes) {
            this.$notifier.success({text: 'Group folder created'})
          }
          if (rocketChannelRes) {
            this.$notifier.success({text: 'Rocket channel created'})
          }
        }))
    }

  }
}
</script>
