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
        <input type="text" v-model="user.uid">
      </p>
      <p>
        <label>Email:</label>
        <input type="email" v-model="user.mail">
      </p>
      <p>
        <label>Password:</label>
        <input type="password" v-model="user.password">
      </p>

      <button @click.prevent="createUser()">Submit</button>
    </div>
  </div>
</template>

<script>
import { LdapUsersService } from '@/common/ldap-api.service.js'
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
        uid: null,
        password: null,
        mail: null
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
      if (!this.user.uid || !this.user.surname || !this.user.name || !this.user.password || !this.user.mail) {
        return null
      }
      let data = {...this.user}
      LdapUsersService.post(data)
        .then(response => {
          let rocketData = response.data.rocket
          if (!rocketData.success) {
            this.$notifier.error({title: 'Error creating rocketchat user', text: rocketData.error})
          }
          this.$router.push({name: 'user', params: {id: this.user.uid}})
        }, (error) => {
          this.$notifier.error({title: 'Error creating user', text: error.response.data.message})
        })
    }

  }
}
</script>
