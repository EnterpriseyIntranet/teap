<template>
  <div>
    <h2>Actions: </h2>
    <div>
      <p>Actions:</p>
      <div class="md-5">
        <ul class="list-group" v-if="actions">
          <li
            class="list-group-item"
            :class="{'list-group-item-success': action.success, 'list-group-item-danger': !action.success}"
            v-for="action in actions" :key="action.id">
            <p><strong>{{ action.event_display }}</strong></p>
            {{ action }} <button v-if="!action.success" @click="retryAction(action)">retry</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ActionsService } from '../common/actions-api.service.js'

export default {
  data () {
    return {
      actions: []
    }
  },

  methods: {
    getActions () {
      ActionsService.get().then((res) => {
        this.actions = res.data
      })
    },

    retryAction (action) {
      ActionsService.post(action.id).then(res => {
        this.$notifier.success({text: 'Action retried'})
        this.getActions()
      }).catch(error => {
        this.$notifier.error({title: 'Action retry failed', text: error.response.data.message})
      })
    }

  },
  created () {
    this.getActions()
  }
}
</script>
