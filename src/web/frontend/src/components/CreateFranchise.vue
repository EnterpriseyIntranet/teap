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
import axios from 'axios'
import { LdapFranchisesService } from '@/common/ldap-api.service.js'
import { GroupFolderService } from '../common/nextcloud-api.service'
import { RocketChannelsService } from '../common/rocketchat-api.service'

export default {

  data () {
    return {
      franchiseCode: null
    }
  },
  methods: {

    createFranchise () {
      LdapFranchisesService.post({franchise_code: this.franchiseCode})
        .then(response => {
          let franchiseDisplayName = response.data.display_name
          let groupFolderReq = GroupFolderService.post({group_name: this.franchiseCode, group_type: 'franchises'})
            .catch(error => {
              this.$notifier.error({title: 'Error creating group folder for division', text: error.response.data.message})
            })
          let rocketChannelReq = RocketChannelsService.post({channel_name: `Franchise-${franchiseDisplayName}`})
            .catch(error => {
              this.$notifier.error({title: 'Error creating rocket chat channel for division', text: error.response.data.error})
            })
          this.$notifier.success({text: response.data.message})
          this.franchiseCode = null
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
