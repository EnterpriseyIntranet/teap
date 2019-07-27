<template>
  <div>
    <h2>Actions: </h2>
    <div>
      <p>Actions:</p>
      <ul v-if="actions">
        <li v-for="action in actions" :key="action.id">
          <p>
            {{ action }}
            <span v-if="!action.success">
              <button @click="retryAction(action)">retry</button>
            </span>
          </p>
        </li>
      </ul>
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
