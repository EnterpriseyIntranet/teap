<template>
    <div>
      <multiselect
        ref="multiselect"
        :value="value"
        @input="updateValue"
        id="ajax"
        track-by="fqdn"
        place-holder="Type to search"
        :options="groups"
        :multiple="true"
        :searchable="true"
        :loading="isLoading"
        open-direction="bottom"
        :internal-search="false"
        :clear-on-select="false"
        :close-on-select="false"
        :options-limit="10"
        :limit="15"
        :show-no-results="false"
        :hide-selected="true"
        @search-change="debounceAsyncSearch"
        @select="selectOption"
        :preserveSearch="true"
      >
        <template slot="option" slot-scope="{ option }">{{ option['cn'][0] }}</template>
        <template slot="tag" slot-scope="{ option }">
          <span class="custom__tag">
            <span>{{ option['cn'][0] }}</span>
            <span class="custom__remove" @click="$emit('remove', option)">❌</span>
          </span>
        </template>
      </multiselect>
    </div>
</template>

<script>
import _ from 'lodash'
import { NxcGroupsService } from '@/common/nextcloud-api.service'

export default {
  name: 'MultipleGroupSearch',

  props: ['value'],

  data () {
    return {
      isLoading: false,
      groups: [],
      notFound: false
    }
  },

  methods: {

    asyncSearch (query) {
      this.$emit('search-change', query)
      this.isLoading = true
      NxcGroupsService.get('', '', {'query': query})
        .then(response => {
          this.groups = response.data
          this.isLoading = false
          if (!this.groups.length) {
            this.$emit('not-found')
          }
        })
        .catch(() => {
          this.$emit('not-found')
        })
    },

    updateValue (value) {
      this.$emit('input', value)
    },

    selectOption (selectedOption, id) {
      this.$emit('select', selectedOption, id)
    }

  },

  created: function () {
    this.debounceAsyncSearch = _.debounce(this.asyncSearch, 500)
    this.asyncSearch()
  }
}
</script>

<style scoped>

</style>
