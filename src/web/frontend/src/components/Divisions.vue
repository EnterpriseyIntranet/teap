<template>
  <div>
    <h2>Divisions: </h2>
    <!-- Users list -->
    <div>
      <p>Regular:</p>
      <ul v-if="divisions">
        <li v-for="(divisionData, divisionName) in regularDivisions" :key="divisionData.fqdn">
          <p><strong>Machine name: </strong>{{ divisionName }}, <strong>Display name: </strong>{{ divisionData.ldap_display_name }}</p>
        </li>
      </ul>
      <p>Config only divisions: </p>
      <ul>
        <li v-for="(divisionData, divisionName) in configOnlyDivisions" :key="divisionData.fqdn">
          <p><strong>Machine name: </strong>{{ divisionName }}, <strong>Display name: </strong>{{ divisionData.config_display_name }} <button @click="createDivision(divisionName, divisionData)">Create</button></p>
        </li>
      </ul>
      <p>Ldap only divisions: </p>
      <ul>
        <li v-for="(divisionData, divisionName) in ldapOnlyDivisions" :key="divisionData.fqdn">
          <p><strong>Machine name: </strong>{{ divisionName }}, <strong>Display name: </strong>{{ divisionData.ldap_display_name }} <button @click="deleteDivision(divisionName)">Delete</button></p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import _ from 'lodash'
import { LdapDivisionsService } from '../common/ldap-api.service.js'
import { GroupFolderService } from '../common/nextcloud-api.service'
import { RocketChannelsService } from '../common/rocketchat-api.service'

export default {
  data () {
    return {
      data: {},
      divisions: []
    }
  },

  computed: {
    regularDivisions: function () {
      return _.pickBy(this.divisions, (value, key) => {
        return value.exists_in_config && value.exists_in_ldap
      })
    },

    configOnlyDivisions: function () {
      return _.pickBy(this.divisions, (value, key) => {
        return value.exists_in_config && !value.exists_in_ldap
      })
    },

    ldapOnlyDivisions: function () {
      return _.pickBy(this.divisions, (value, key) => {
        return value.exists_in_ldap && !value.exists_in_config
      })
    }
  },

  methods: {
    getDivisions () {
      LdapDivisionsService.get().then((res) => {
        this.divisions = res.data.divisions
      })
    },
    createDivision (machineName, data) {
      LdapDivisionsService.post({machine_name: machineName}).then(res => {
        this.getDivisions()
        this.$notifier.success({text: 'Division created'})
        let groupFolderReq = GroupFolderService.post({group_name: machineName, group_type: 'divisions'})
          .catch(error => {
            this.$notifier.error({title: 'Error creating group folder for division', text: error.response.data.message})
          })
        let rocketChannelReq = RocketChannelsService.post({channel_name: `Division-${data.config_display_name}`})
          .catch(error => {
            this.$notifier.error({title: 'Error creating rocket chat channel for division', text: error.response.data.error})
          })
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
    },

    deleteDivision (divisionName) {
      LdapDivisionsService.delete(divisionName).then(res => {
        this.$notifier.success({text: 'Division successfully deleted'})
        this.getDivisions()
      }).catch(error => {
        this.$notifier.error({title: 'Division deleting failed', text: error.response.data.message})
      })
    }

  },
  created () {
    this.getDivisions()
  }
}
</script>
