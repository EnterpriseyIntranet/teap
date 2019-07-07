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
import _ from 'lodash'
import { LdapConfigDivisionsService, LdapDivisionService } from '../common/ldap-api.service.js'

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
      LdapConfigDivisionsService.get().then((res) => {
        this.divisions = res.data.divisions
      })
    },
    createDivision (machineName, data) {
      LdapConfigDivisionsService.post({machine_name: machineName})
        .then(response => {
          this.getDivisions()
          this.$notifier.success({text: 'Division created'})

          let channelRes = response.data.rocket
          let folderRes = response.data.folder

          if (!channelRes.success) {
            this.$notifier.error({title: 'Error creating rocket chat channel for division', text: channelRes.error})
          }

          if (!folderRes.success) {
            this.$notifier.error({title: 'Error creating group folder for division', text: folderRes.error})
          }
        }, (error) => {
          this.$notifier.error({title: 'Error creating division', text: error.response.data.message})
        })
    },

    deleteDivision (divisionName) {
      LdapDivisionService.delete(divisionName).then(res => {
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
