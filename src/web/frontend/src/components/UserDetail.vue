<template>
  <div>
    <div v-if="user">
      <h2>User: {{ user.uid }}</h2>

        <p><strong>Franchises:</strong></p>
        <p>
          <franchises-select
            v-model="user.franchises"
            @select="addToFranchise"
            @remove="removeFromFranchise">
          </franchises-select></p>

        <p><strong>Divisions:</strong></p>
        <p><divisions-select
          v-model="user.divisions"
          @select="addToDivision"
          @remove="removeFromDivision"
        >
        </divisions-select></p>

        <p><strong>Teams:</strong></p>
        <p><teams-select
          v-model="user.teams"
          @select="addToTeam"
          @remove="removeFromTeam"
        >
        </teams-select></p>

        <modal name="remove">
            <p>Delete user</p>
            <p>Delete empty groups? <input v-model="deleteEmptyGroups" type="checkbox"/></p>
            <button @click="deleteUser()">Delete</button>
            <button @click="$modal.hide('remove')">Cancel</button>
        </modal>
        <p><button v-on:click.prevent="openDeleteModal()">Delete</button></p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { NxcUsersService, NxcGroupsService } from '@/common/nextcloud-api.service'
import { LdapUserFranchisesService, LdapUserDivisionsService, LdapUserTeamsService } from '@/common/ldap-api.service'
import { RocketUserChannelsService } from '@/common/rocketchat-api.service'

import MultipleGroupSearch from '@/components/MultipleGroupSearch.vue'
import FranchisesSelect from './franchisesSelect'
import DivisionsSelect from './divisionsSelect'
import TeamsSelect from './teamsSelect'

export default {
  name: 'UserDetail',
  props: ['id'],
  components: {
    TeamsSelect,
    FranchisesSelect,
    DivisionsSelect,
    MultipleGroupSearch
  },
  data () {
    return {
      user: null,
      deleteEmptyGroups: false
    }
  },

  methods: {

    getUser () {
      NxcUsersService.get(this.id)
        .then(
          response => {
            this.user = response.data
          }
        )
        .catch((error) => {
          if (error.response.status === 404) {
            this.$router.push({'name': 'notFound'})
          } else {
            this.$notifier.error({text: error.response.data.message})
          }
        })
    },

    addToGroup (groupService, groupMachineName) {
      return groupService.post(this.id, {machineName: groupMachineName})
        .then(response => {
          this.$notifier.success({text: 'successfully added'})
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to add', text: error.response.data.message})
        })
    },

    removeFromGroup (groupService, groupMachineName, groupName) {
      if (!confirm('Are you sure you want to delete user from this group?')) {
        return
      }
      return groupService.delete(this.id, {machineName: groupMachineName})
        .then(response => {
          this.$notifier.success({text: 'successfully deleted'})
          this.user[groupName] = this.user[groupName].filter((each) => (each.machineName !== groupMachineName))
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to delete', text: error.response.data.message})
        })
    },

    addToRocketGroup (groupId) {
      RocketUserChannelsService.post(this.user.uid, groupId)
        .then(response => {
          this.$notifier.success({title: 'Successfully added to rocket group'})
        })
        .catch(error => {
          this.$notifier.error({title: 'Failed to add to rocket group', text: error.response.data.message})
        })
    },

    deleteFromRocketGroup (groupId) {
      RocketUserChannelsService.delete(this.user.uid, groupId)
        .then(response => {
          this.$notifier.success({title: 'Deleted from corresponding rocket group'})
        })
        .catch(error => {
          this.$notifier.error({title: 'Failed to delete from corresponding rocket group',
            text: error.response.data.message})
        })
    },

    addToFranchise (group) {
      this.addToGroup(LdapUserFranchisesService, group.machineName)
        .then(() => {
          this.addToRocketGroup(`Franchise-${group.displayName}`)
        })
    },

    removeFromFranchise (group, callback) {
      this.removeFromGroup(LdapUserFranchisesService, group.machineName, 'franchises')
        .then(() => {
          this.deleteFromRocketGroup(`Franchise-${group.displayName}`)
        })
    },

    addToDivision (group) {
      this.addToGroup(LdapUserDivisionsService, group.machineName)
        .then(() => {
          this.addToRocketGroup(`Division-${group.displayName}`)
        })
    },

    removeFromDivision (group) {
      this.removeFromGroup(LdapUserDivisionsService, group.machineName, 'divisions')
        .then(() => {
          this.deleteFromRocketGroup(`Division-${group.displayName}`)
        })
    },

    addToTeam (group) {
      this.addToGroup(LdapUserTeamsService, group.machineName)
        .then(() => {
          this.getUser()
          RocketUserChannelsService.addToTeamChats(this.user.uid, group.machineName)
            .then(() => {
              this.$notifier.success({title: 'Successfully added to team chats'})
            }, (error) => {
              this.$notifier.error({title: 'Failed to add to team chats', text: error.response.data.message})
            })
        })
    },

    removeFromTeam (group) {
      this.removeFromGroup(LdapUserTeamsService, group.machineName, 'teams')
    },

    addToGroupSubadmins (group) {
      NxcGroupsService.createSubadmin(this.id, group)
        .then(response => {
          if (response.data.status) {
            this.$notifier.success()
          } else {
            this.$notifier.error({text: response.data.message})
          }
        })
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
        .finally(response => {
          this.getUser()
        })
    },

    removeFromGroupSubadmins (group) {
      if (!confirm('Are you sure you want to delete user from this group subadmins?')) {
        return
      }
      NxcGroupsService.deleteSubadmin(this.id, group)
        .then(response => {
          this.$notifier.success({text: 'Successfully deleted'})
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to delete', text: error.response.data.message})
        })
        .finally(response => {
          this.getUser()
        })
    },

    openDeleteModal () {
      this.$modal.show('remove')
    },

    deleteUser () {
      let requests = [NxcUsersService.delete(this.user.id)]
      if (this.deleteEmptyGroups) {
        requests.push(NxcGroupsService.deleteEmpty({groups: this.user.groups}))
      }
      axios.all(requests)
        .then(axios.spread((acct, perms) => {
          this.$router.push({name: 'home'})
        }))
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
    }

  },

  created () {
    this.getUser()
  }

}
</script>

<style scoped>

</style>
