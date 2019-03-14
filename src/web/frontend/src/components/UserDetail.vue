<template>
  <div>
    <div v-if="user">
      <h2>User: {{ user.id }}</h2>
        <p>Enabled: {{ user.enabled }}</p>
        <p>Address: {{ user.address || "None" }}</p>

        <p>Groups:</p>
        <ul v-if="user.groups.length > 0">
          <li v-for="group in user.groups" :key="group">
            <p>{{ group }} <button v-on:click="removeFromGroup(group)">delete</button></p>
          </li>
        </ul>
        <p v-else-if="user.groups.length <= 0">None</p>

        <p>Subadmin Groups:</p>
        <ul v-if="user.subadmin.length > 0">
          <li v-for="group in user.subadmin" :key="group">
            <p>{{ group }} <button v-on:click="removeFromGroupSubadmins(group)">delete</button></p>
          </li>
        </ul>
        <p v-else-if="user.subadmin.length <= 0">None</p>

        <p>Add to group: </p>
        <input type="text" v-model="groupName"/>
        <p v-if="groupNotFound" style="color: red;">Group not found</p>
        <p><button v-on:click="addToGroup()">Add to group</button><button v-on:click="addToGroupSubadmins()">Add to subadmins</button></p>
    </div>
  </div>
</template>

<script>
import { NxcUsersService, NxcUserGroupsService, NxcGroupsService } from '@/common/nextcloud-api.service'

export default {
  name: 'UserDetail',
  props: ['id'],
  data () {
    return {
      user: null,
      groupName: '',
      groupNotFound: false
    }
  },

  methods: {

    getUser () {
      NxcUsersService.get(this.id)
        .then(
          response => {
            this.user = response.data.data
          }
        )
    },

    removeFromGroup (group) {
      if (!confirm('Are you sure you want to delete user from this group?')) {
        return
      }
      NxcUserGroupsService.delete(this.id, group)
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
          this.getUser()
        })
    },

    addToGroup () {
      this.groupNotFound = false
      NxcUserGroupsService.post(this.id, this.groupName)
        .then(response => {
          if (response.data.status) {
            console.log('successfully added')
            this.groupName = ''
          } else {
            console.log('failed to add')
          }
        })
        .catch(error => {
          console.log('failed', error)
          if (error.response.status === 404) {
            this.groupNotFound = true
          }
        })
        .finally(response => {
          console.log('finally')
          this.getUser()
        })
    },

    addToGroupSubadmins () {
      this.groupNotFound = false
      NxcGroupsService.createSubadmin(this.id, this.groupName)
        .then(response => {
          if (response.data.status) {
            console.log('successfully added')
            this.groupName = ''
          } else {
            console.log('failed to add')
          }
        })
        .catch(error => {
          console.log('failed', error)
          if (error.response.status === 404) {
            this.groupNotFound = true
          }
        })
        .finally(response => {
          console.log('finally')
          this.getUser()
        })
    },

    removeFromGroupSubadmins (group) {
      if (!confirm('Are you sure you want to delete user from this group subadmins?')) {
        return
      }
      NxcGroupsService.deleteSubadmin(this.id, group)
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
          this.getUser()
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
