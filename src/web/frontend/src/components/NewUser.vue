<template>
  <div>
    <!-- Create user -->
    <div>
      <p>New user: </p>
      <p>
        <label>Username:</label>
        <input type="text" v-model="user.username">
      </p>
      <p>
        <label>Password:</label>
        <input type="password" v-model="user.password">
      </p>
      <!-- Groups -->
        <p>Groups:</p>
        <multiple-group-search v-model="user.groups" @search-change="groupSearchChange" @not-found="groupNotFound" @remove="removeGroup"></multiple-group-search>

        <div v-if="!groupExists && newGroup.name">
          <p>Group doesn't exist, but you can create it: </p>
          <p>New group: {{ newGroup.name }}</p>

          <select v-model="newGroup.type">
            <option value="divisions">Divisions</option>
            <option value="countries">Countries</option>
            <option selected value="other">Other</option>
          </select>

          <button @click.prevent="createGroup()">Create</button>

        </div>

      <!-- End Groups -->
      <button @click.prevent="createUser()">Submit</button>
    </div>
  </div>
</template>

<script>
import { NxcUsersService, GroupWithFolderService } from '../common/nextcloud-api.service.js'
import MultipleGroupSearch from '@/components/MultipleGroupSearch.vue'

export default {
  components: {
    MultipleGroupSearch
  },

  data () {
    return {
      user: {
        username: null,
        password: null,
        groups: []
      },
      groupExists: true,
      newGroup: {
        name: null,
        type: 'other'
      }
    }
  },
  methods: {

    createUser () {
      if (!this.user.username) {
        return null
      }
      let data = {
        username: this.user.username,
        password: this.user.password,
        groups: this.user.groups
      }
      NxcUsersService.post(data)
        .then(response => {
          if (response.data.status) {
            this.$router.push({name: 'user', params: {id: this.user.username}})
          } else {
            this.$notifier.error({text: response.data.message})
          }
        })
        .catch((error) => {
          this.$notifier.error({text: error.data.message})
        })
    },

    createGroup () {
      let data = {group_name: this.newGroup.name, group_type: this.newGroup.type}
      GroupWithFolderService.post(data)
        .then(response => {
          this.groupExists = true
          this.user.groups.push(this.newGroup.name)
        })
        .catch((error) => {
          this.$notifier.error({text: error.data.message})
        })
    },

    groupSearchChange (query) {
      this.newGroup.name = query
      this.groupExists = true
    },

    groupNotFound (query) {
      this.groupExists = false
    },

    removeGroup (group) {
      this.user.groups.splice(this.user.groups.indexOf(group), 1)
    }

  }
}
</script>
