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
    <router-link :to="{name: 'newUser'}"><a>New user</a></router-link>
  </div>
</template>

<script>
import { NxcUsersService } from '../common/nextcloud-api.service.js'

export default {
  data () {
    return {
      users: null
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
    }

  },
  created () {
    this.getUsers()
  }
}
</script>
