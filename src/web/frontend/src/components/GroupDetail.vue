<template>
    <div>
      <div v-if="group">
        <h2>Group: {{ id }}</h2>

        <p>Users:</p>
        <ul v-if="group.users.length > 0">
          <li v-for="user in group.users" :key="user">
            <p>{{ user }} <button v-on:click="deleteGroupUser(user)">delete</button></p>
        </li>
        </ul>
        <p v-else-if="group.users.length <= 0">None</p>

        <p>Subadmins:</p>
        <ul v-if="group.subadmins && group.subadmins.length > 0">
          <li v-for="subadmin in group.subadmins" :key="subadmin">
            <p>{{ subadmin }} <button v-on:click="deleteSubadmin(subadmin)">delete</button></p>
        </li>
        </ul>
        <p v-else-if="group.subadmins && group.subadmins.length <= 0">None</p>

      </div>
    </div>
</template>

<script>
import { NxcGroupsService, NxcUserGroupsService } from '@/common/nextcloud-api.service'

export default {
  name: 'GroupDetail',
  props: ['id'],
  data () {
    return {
      group: null
    }
  },
  methods: {

    getGroup () {
      NxcGroupsService.get(this.id)
        .then(response => {
          this.group = response.data.data
          this.getGroupSubadmins()
          console.log('success', response)
        })
        .catch(error => {
          console.log('failed to load group', error)
        })
    },

    getGroupSubadmins () {
      NxcGroupsService.get(this.id, 'subadmins')
        .then(response => {
          console.log('subadmins success, response: ', response)
          this.$set(this.group, 'subadmins', response.data.data)
        })
        .catch(error => {
          console.log('subadmins error, error: ', error)
        })
    },

    deleteGroupUser (user) {
      if (!confirm('Are you sure you want to delete user from this group?')) {
        return
      }
      NxcUserGroupsService.delete(user, this.id)
        .then(response => {
          console.log('success', response)
          this.getGroup()
        })
        .catch(error => {
          console.log('error', error)
        })
    },

    deleteSubadmin (user) {
      if (!confirm('Are you sure you want to delete user from this group subadmins?')) {
        return
      }
      NxcGroupsService.deleteSubadmin(user, this.id)
        .then(response => {
          console.log('success', response)
          this.getGroup()
        })
        .catch(error => {
          console.log('error', error)
        })
    }
  },
  created () {
    console.log(this.id)
    this.getGroup()
  }
}
</script>

<style scoped>

</style>
