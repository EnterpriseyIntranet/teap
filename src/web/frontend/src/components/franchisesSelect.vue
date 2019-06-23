<template>
    <div>
        <groups-select
          :value="value"
          @search-change="asyncSearch"
          @input="updateValue"
          @select="selectOption"
          @remove="remove"
          v-bind:isLoading="isLoading"
          v-bind:groups="groups"
        ></groups-select>
    </div>
</template>

<script>
import GroupsSelect from '@/components/groupsSelect.vue'
import { LdapFranchisesService } from '@/common/ldap-api.service.js'

export default {
  name: 'franchisesSelect',
  components: {GroupsSelect},
  props: ['value'],

  data () {
    return {
      isLoading: false,
      groups: []
    }
  },

  methods: {

    asyncSearch (query) {
      this.isLoading = true
      LdapFranchisesService.get({'query': query})
        .then(response => {
          this.groups = response.data
          this.isLoading = false
          if (!this.groups.length) {
            this.$emit('not-found')
          }
        })
        .catch(() => {
          this.$emit('exception')
        })
    },

    updateValue (value) {
      this.$emit('input', value)
    },

    selectOption (selectedOption, id) {
      this.$emit('select', selectedOption, id)
    },

    remove (value) {
      this.$emit('remove', value)
    }

  }

}
</script>

<style scoped>

</style>
