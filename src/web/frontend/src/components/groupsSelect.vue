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
        <template slot="option" slot-scope="{ option }">{{ option.displayName }}</template>
        <template slot="tag" slot-scope="{ option }">
          <span class="custom__tag">
            <span>{{ option.displayName }}</span>
            <span class="custom__remove" @click="$emit('remove', option)">❌</span>
          </span>
        </template>
      </multiselect>
    </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'groupsSelect',

  props: ['value', 'groups'],

  data () {
    return {
      isLoading: false,
      notFound: false
    }
  },

  methods: {

    asyncSearch (query) {
      this.$emit('search-change', query)
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
