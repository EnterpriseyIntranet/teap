<template>
  <div>
    <h2>Groups</h2>
    <!-- Groups list -->
    <div>
      <p>List:</p>
      <ul>
        <li v-for="group in groups" :key="group">
          {{ group }} <button v-on:click="deleteGroup(group)">delete</button>
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
          this.groups = response.data.data.groups
        }
        )
        .catch(error =>
          console.log(error)
        )
    },
    deleteGroup (group) {
      if (confirm('Are you sure you want to delete this group?')) {
        NxcGroupsService.delete(group)
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
            this.getGroups()
          })
      }
    },

    createGroup () {
      if (!this.newGroupName) {
        return null
      }
      let data = {
        group_name: this.newGroupName
      }
      NxcGroupsService.post(data)
        .then(response => {
          if (response.data.status) {
            console.log('successfully created!')
            this.newGroupName = null
            this.getGroups()
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
    this.getGroups()
  }
}
</script>

<style scoped>

</style>
