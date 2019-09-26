import Vue from 'vue'
import App from './App'
import router from './router'
import Multiselect from 'vue-multiselect'
import VModal from 'vue-js-modal'
import Paginate from 'vuejs-paginate'

import Notifier from './common/notifier'
import ApiService from './common/api.service'

Vue.config.productionTip = false
Vue.component('multiselect', Multiselect)
Vue.component('paginate', Paginate)
Vue.use(VModal)

Notifier.init()
ApiService.init()

Vue.prototype.$notifier = Notifier
/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})
