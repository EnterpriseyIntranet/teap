<template>
  <div>
    <h2>Teams: </h2>
    <!-- Users list -->
    <div>
      <p>Teams:</p>
      <ul v-if="teams">
        <li v-for="team in teams" :key="team.fqdn">
          <p>
            <strong>Display name:</strong> {{ team.displayName }};
            <strong>Machine name:</strong> {{ team.machineName }}
            <button @click="deleteTeam(team)">Delete</button>
          </p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { LdapTeamsService } from '../common/ldap-api.service.js'

export default {
  data () {
    return {
      teams: []
    }
  },

  methods: {
    getTeams () {
      LdapTeamsService.get().then((res) => {
        this.teams = res.data
      })
    },

    deleteTeam (team) {
      LdapTeamsService.delete(team.machineName).then(res => {
        this.$notifier.success({text: 'Team successfully deleted'})
        this.getTeams()
      }).catch(error => {
        this.$notifier.error({title: 'Team deleting failed', text: error.response.data.message})
      })
    }

  },
  created () {
    this.getTeams()
  }
}
</script>
