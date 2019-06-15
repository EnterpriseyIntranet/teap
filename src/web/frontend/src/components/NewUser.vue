<template>
  <div>
    <!-- Create user -->
    <div>
      <p>New user: </p>
      <p>
        <label>Name:</label>
        <input type="text" v-model="user.name">
      </p>
      <p>
        <label>Surname:</label>
        <input type="text" v-model="user.surname">
      </p>
      <p>
        <label>Username:</label>
        <input type="text" v-model="user.username">
      </p>
      <p>
        <label>Email:</label>
        <input type="email" v-model="user.email">
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
          <p v-if="groupNameError" style="color: red">{{ groupNameError }}</p>

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
import axios from 'axios'
import { NxcUsersService, GroupWithFolderService } from '@/common/nextcloud-api.service.js'
import { RocketUsersService } from '@/common/rocketchat-api.service.js'
import MultipleGroupSearch from '@/components/MultipleGroupSearch.vue'

export default {
  components: {
    MultipleGroupSearch
  },

  data () {
    return {
      user: {
        name: null,
        surname: null,
        username: null,
        password: null,
        email: null,
        groups: []
      },
      groupExists: true,
      newGroup: {
        name: null,
        type: 'other'
      },
      groupNameError: false
    }
  },
  methods: {

    createUser () {
      if (!this.user.username || !this.user.surname || !this.user.name || !this.user.password) {
        return null
      }
      let groups = []
      for (let group of this.user.groups) {
        groups.push(group.fqdn)
      }
      let data = {...this.user}
      data.groups = groups
      NxcUsersService.post(data)
        .then(response => {
          let createRocketUser = RocketUsersService.post(data)
            .catch(error => {
              this.$notifier.error({title: 'Error creating rocket chat user', text: error.response.data.message})
            })
          return axios.all([createRocketUser])
        }, (error) => {
          this.$notifier.error({title: 'Error creating user', text: error.response.data.message})
        })
        .then(axios.spread((rocketRes) => {
          this.$router.push({name: 'user', params: {id: this.user.username}})
        }))
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
    },

    createGroup () {
      this.groupNameError = false
      let data = {group_name: this.newGroup.name, group_type: this.newGroup.type}

      if (!this.validateGroupData(data)) {
        return
      }

      GroupWithFolderService.post(data)
        .then(response => {
          this.groupExists = true
          this.user.groups.push(this.newGroup.name)
        })
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
    },

    validateGroupData (data) {
      if (data.group_type === 'divisions' && !data.group_name.startsWith('Division')) {
        this.groupNameError = 'Division group name must start with "Division"'
        return false
      } else if (data.group_type === 'countries' && !data.group_name.startsWith('Country')) {
        this.groupNameError = 'Country group name must start with "Country"'
        return false
      }
      return true
    },

    groupSearchChange (query) {
      this.newGroup.name = query
      this.groupNameError = false
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
