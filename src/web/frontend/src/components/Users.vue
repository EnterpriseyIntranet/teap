<template>
  <div>
    <h2>Users: </h2>
    <!-- Users list -->
    <div>
      <p>List:</p>
      <ul>
        <li v-for="user in users" :key="user">
          <router-link :to="{name: 'user', params: {id: user}}">{{ user }}</router-link> <button v-on:click="deleteUser(user)">delete</button>
        </li>
      </ul>
    </div>

    <!-- Create user -->
    <div>
      <p>Create user: </p>
      <p>
        <label>Username:</label>
        <input type="text" v-model="newUsername">
      </p>
      <p>
        <label>Password:</label>
        <input type="password" v-model="newPassword">
      </p>
      <button @click.prevent="createUser()">Submit</button>
    </div>
  </div>
</template>

<script>
import { NxcUsersService } from '../common/nextcloud-api.service.js'

export default {
  data () {
    return {
      users: null,
      newUsername: null,
      newPassword: null
    }
  },
  methods: {
    getUsers () {
      NxcUsersService.get()
        .then(response => {
          this.users = response.data.data.users
        }
        )
        .catch(error =>
          console.log(error)
        )
    },
    deleteUser (user) {
      if (!confirm('Are you sure you want to delete this user?')) {
        return
      }
      NxcUsersService.delete(user)
        .then(response => {
          if (response.data.status) {
            console.log('successfully deleted')
          } else {
            console.log('failed to delete')
          }
        })
        .catch(error => {
          console.log('failed to delete', error)
        })
        .finally(response => {
          console.log('finally')
          this.getUsers()
        })
    },

    createUser () {
      if (!this.newUsername) {
        return null
      }
      let data = {
        username: this.newUsername,
        password: this.newPassword
      }
      NxcUsersService.post(data)
        .then(response => {
          if (response.data.status) {
            console.log('successfully created!')
            this.newUsername = this.newPassword = null
            this.getUsers()
          } else {
            console.log('failed to create')
          }
        })
        .catch(error => {
          console.log('failed to create ', error)
        })
    }
  },
  created () {
    this.getUsers()
  }
}
</script>
