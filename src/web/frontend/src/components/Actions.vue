<template>
  <div>
    <div class="container-fluid wrapper">
      <h2>Actions: </h2>
      <div class="row justify-content-center">
        <div style="padding-right: 50px; padding-left: 50px">
            <ul class="list-group" v-if="actions">
              <li
                class="list-group-item"
                :class="{'list-group-item-success': action.status, 'list-group-item-danger': !action.status}"
                v-for="action in actions" :key="action.id">
                <p><strong>{{ action.event_display }}</strong></p>
                {{ action }} <button v-if="!action.success" @click="retryAction(action)">retry</button>
              </li>
            </ul>
          </div>
      </div>

      <!-- pagination -->
      <div v-if="count > 20">
        <paginate
          :page-count="pagesCount"
          :click-handler="changePage"
          :page-range="2"
          :margin-pages="2"
          :prev-text="'Prev'"
          :next-text="'Next'"
          :prev-class="'page-item page-link'"
          :next-class="'page-item page-link'"
          :container-class="'pagination justify-content-center'"
          :page-class="'page-item page-link'">
        </paginate>
      </div>
    </div>
  </div>
</template>

<script>
import { ActionsService } from '../common/actions-api.service.js'

export default {
  data () {
    return {
      actions: [],
      count: 0,
      page: 1,
      pagesCount: 1
    }
  },

  methods: {
    getActions () {
      ActionsService.get({page: this.page}).then((res) => {
        this.actions = res.data.data
        this.count = res.data.count
        this.pagesCount = this.count / 20
      })
    },

    retryAction (action) {
      ActionsService.post(action.id).then(res => {
        this.$notifier.success({text: 'Action retried'})
        this.getActions()
      }).catch(error => {
        this.$notifier.error({title: 'Action retry failed', text: error.response.data.message})
      })
    },

    changePage (page) {
      this.page = page
      this.getActions()
    }

  },
  created () {
    this.getActions()
  }
}
</script>
