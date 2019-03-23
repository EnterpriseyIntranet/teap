import Vue from 'vue'
import App from './App'
import router from './router'
import Multiselect from 'vue-multiselect'
import VModal from 'vue-js-modal'

import ApiService from './common/api.service'

Vue.config.productionTip = false
Vue.component('multiselect', Multiselect)
Vue.use(VModal)

ApiService.init()

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})
