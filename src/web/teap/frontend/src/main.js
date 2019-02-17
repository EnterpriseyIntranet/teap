import Vue from 'vue'
import App from './App'
import router from './router'
import axios from 'axios'

axios.defaults.headers.post['Content-Type'] = 'application/json'

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})
