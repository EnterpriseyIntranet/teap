<template>
  <div>
    <div v-if="user">
      <h2>User: {{ user.id }}</h2>
        <p>Enabled: {{ user.enabled }}</p>
        <p>Address: {{ user.address || "None" }}</p>

        <p>Groups:</p>
        <multiple-group-search v-model="user.groups" @remove="removeFromGroup" @select="addToGroup"></multiple-group-search>

        <p>Subadmin Groups:</p>
        <ul v-if="user.subadmin.length > 0">
          <li v-for="group in user.subadmin" :key="group">
            <p>{{ group }} <button v-on:click="removeFromGroupSubadmins(group)">delete</button></p>
          </li>
        </ul>
        <p v-else-if="user.subadmin.length <= 0">None</p>

        <p><button v-on:click.prevent="openDeleteModal()">Delete</button></p>

        <modal name="remove">
            <p>Delete user</p>
            <p>Delete empty groups? <input v-model="deleteEmptyGroups" type="checkbox"/></p>
            <button @click="deleteUser()">Delete</button>
            <button @click="$modal.hide('remove')">Cancel</button>
        </modal>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { NxcUsersService, NxcUserGroupsService, NxcGroupsService } from '@/common/nextcloud-api.service'
import MultipleGroupSearch from '@/components/MultipleGroupSearch.vue'

export default {
  name: 'UserDetail',
  props: ['id'],
  components: {
    MultipleGroupSearch
  },
  data () {
    return {
      user: null,
      groupName: '',
      groupNotFound: false,
      deleteEmptyGroups: false
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
        .catch(() => {
          this.$router.push({'name': 'notFound'})
        })
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

    addToGroup (group) {
      NxcUserGroupsService.post(this.id, group)
        .then(response => {
          if (response.data.status) {
            console.log('successfully added')
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
          console.log(error)
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
