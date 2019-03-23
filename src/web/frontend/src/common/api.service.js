import Vue from 'vue'
import axios from 'axios'
import VueAxios from 'vue-axios'
import { API_URL } from '@/common/config'

const ApiService = {
  init () {
    Vue.use(VueAxios, axios)
    Vue.axios.defaults.baseURL = API_URL
    Vue.axios.defaults.headers.common['Content-Type'] = 'application/json'
  },

  get (resource, slug = '', params) {
    return Vue.axios.get(`${resource}/${slug}`, {'params': params}).catch(error => {
      throw new Error(error)
    })
  },

  post (resource, params) {
    console.log('params: ', params)
    return Vue.axios.post(`${resource}/`, params)
  },

  update (resource, slug = '', params) {
    return Vue.axios.put(`${resource}/${slug}`, params)
  },

  put (resource, params) {
    return Vue.axios.put(`${resource}`, params)
  },

  delete (resource, slug = '', data) {
    return Vue.axios.delete(`${resource}/${slug}`, {'data': data}).catch(error => {
      throw new Error(error)
    })
  }
}

export default ApiService
