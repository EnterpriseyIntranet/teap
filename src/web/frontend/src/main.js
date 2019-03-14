import Vue from 'vue'
import App from './App'
import router from './router'

import ApiService from './common/api.service'

Vue.config.productionTip = false

ApiService.init()

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})
