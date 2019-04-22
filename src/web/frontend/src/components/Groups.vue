<template>
  <div>
    <h2>Groups</h2>
    <!-- Groups list -->
    <div>
      <p>List:</p>
      <ul>
        <li v-for="group in groups" :key="group.fqdn">
          <router-link :to="{name: 'group', params: {id: group.data.cn[0]}}">{{ group.data.cn[0] }}</router-link> <button v-on:click="deleteGroup(group)">delete</button>
        </li>
      </ul>
    </div>

    <!-- Create group -->
    <div>
      <p>Create group: </p>
      <p>
        <label>Group name:</label>
        <input type="text" v-model="newGroupName">
        <button @click.prevent="createGroup()">Submit</button>
      </p>
    </div>
  </div>
</template>

<script>
import { NxcGroupsService } from '../common/nextcloud-api.service'

export default {
  data () {
    return {
      groups: null,
      newGroupName: null
    }
  },

  methods: {
    getGroups () {
      NxcGroupsService.get()
        .then(response => {
          this.groups = response.data
        })
        .catch(error =>
          console.log(error)
        )
    },
    deleteGroup (group) {
      if (!confirm('Are you sure you want to delete this group?')) {
        return
      }
      NxcGroupsService.delete(group)
        .then(response => {
          this.$notifier.success()
        })
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
        .finally(() => {
          this.getGroups()
        })
    },

    createGroup () {
      if (!this.newGroupName) {
        return
      }
      let data = {
        group_name: this.newGroupName
      }
      NxcGroupsService.post(data)
        .then(response => {
          if (response.data.status) {
            this.$notifier.success()
            this.newGroupName = null
            this.getGroups()
          } else {
            this.$notifier.error({text: response.data.message})
          }
        })
        .catch((error) => {
          this.$notifier.error({text: error.response.data.message})
        })
    }
  },
  created () {
    this.getGroups()
  }
}
</script>

<style scoped>

</style>
