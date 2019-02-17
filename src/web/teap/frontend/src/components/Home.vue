<template>
  <div>
    <!-- Users list -->
    <div>
      <p>Users list:</p>
      <ul>
        <li v-for="user in users" :key="user">
          {{ user }} <button v-on:click="deleteUser(user)">delete</button>
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
import axios from 'axios'

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
      axios.get('http://localhost:5000/api/users')
        .then(response => {
          this.users = response.data.users
        }
        )
        .catch(error =>
          console.log(error)
        )
    },
    deleteUser (user) {
      if (confirm('Are you sure you want to delete this user?')) {
        axios.delete(`http://localhost:5000/api/users/${user}`)
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
      }
    },

    createUser () {
      console.log('create user!')
      if (!this.newUsername) {
        return null
      }
      let data = {
        username: this.newUsername,
        password: this.newPassword
      }
      axios.post('http://localhost:5000/api/users', JSON.stringify(data))
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
