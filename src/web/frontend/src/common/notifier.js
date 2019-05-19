import Vue from 'vue'
import Notifications from 'vue-notification'

const Notifier = {
  init () {
    Vue.use(Notifications)
  },

  error (data = {}) {
    Vue.notify({
      type: 'error',
      title: data.title || 'Error',
      text: data.text || 'Oops, something wrong happened...'
    })
  },

  warning (data = {}) {
    Vue.notify(
      {
        type: 'warn',
        title: data.title || 'Warning',
        text: data.text || 'Oops, something wrong happened...'
      }
    )
  },

  success (data = {}) {
    Vue.notify(
      {
        type: 'success',
        title: data.title || 'Success',
        text: data.text || 'Operation successful'
      }
    )
  }
}

export default Notifier
