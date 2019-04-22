<template>
  <div>
    <div v-if="user">
      <h2>User: {{ user.data['uid'][0] }}</h2>

        <p>Groups:</p>
        <multiple-group-search v-model="user.groups" @remove="removeFromGroup" @select="addToGroup"></multiple-group-search>

<!--        <p>Subadmin Groups:</p>-->
<!--        <multiple-group-search v-model="user.subadmin" @remove="removeFromGroupSubadmins" @select="addToGroupSubadmins"></multiple-group-search>-->

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
      deleteEmptyGroups: false
    }
  },

  methods: {

    getUser () {
      NxcUsersService.get(this.id)
        .then(
          response => {
            this.user = response.data
          }
        )
        .catch((error) => {
          if (error.response.status === 404) {
            this.$router.push({'name': 'notFound'})
          } else {
            this.$notifier.error({text: error.response.data.message})
          }
        })
    },

    removeFromGroup (group) {
      if (!confirm('Are you sure you want to delete user from this group?')) {
        return
      }
      NxcUserGroupsService.delete(this.id, group.fqdn)
        .then(response => {
          this.$notifier.success({text: 'successfully deleted'})
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to delete', text: error.response.data.message})
        })
        .finally(response => {
          this.getUser()
        })
    },

    addToGroup (group) {
      NxcUserGroupsService.post(this.id, group.fqdn)
        .then(response => {
          this.$notifier.success({text: 'successfully added'})
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to add', text: error.response.data.message})
        })
        .finally(response => {
          this.getUser()
        })
    },

    addToGroupSubadmins (group) {
      NxcGroupsService.createSubadmin(this.id, group)
        .then(response => {
          if (response.data.status) {
            this.$notifier.success()
          } else {
            this.$notifier.error({text: response.data.message})
          }
        })
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
        .finally(response => {
          this.getUser()
        })
    },

    removeFromGroupSubadmins (group) {
      if (!confirm('Are you sure you want to delete user from this group subadmins?')) {
        return
      }
      NxcGroupsService.deleteSubadmin(this.id, group)
        .then(response => {
          this.$notifier.success({text: 'Successfully deleted'})
        })
        .catch((error) => {
          this.$notifier.error({title: 'Failed to delete', text: error.response.data.message})
        })
        .finally(response => {
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
          this.$notifier.error({text: error.response.data.message})
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
