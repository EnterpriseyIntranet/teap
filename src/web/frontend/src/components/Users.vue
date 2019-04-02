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
          if (response.data.status) {
            this.users = response.data.data.users
          } else {
            this.$notifier.error({text: response.data.message})
          }
        }
        )
        .catch((error) => {
          this.$notifier.error({text: error.data.message})
        })
    },
    deleteUser (user) {
      if (!confirm('Are you sure you want to delete this user?')) {
        return
      }
      NxcUsersService.delete(user)
        .then(response => {
          console.log(response.data)
          if (response.data.status) {
            this.$notifier.success({text: 'User successfully deleted'})
          } else {
            this.$notifier.error({title: 'Failed to delete', text: response.data.message})
          }
        })
        .catch((error) => {
          this.$notifier.error({text: error.data.message})
        })
        .finally(response => {
          this.getUsers()
        })
    }

  },
  created () {
    this.getUsers()
  }
}
</script>
