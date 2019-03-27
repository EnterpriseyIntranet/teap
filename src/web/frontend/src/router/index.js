import Vue from 'vue'
import Router from 'vue-router'

const routerOptions = [
  {name: 'home', path: '/', component: 'Home'},
  {name: 'newUser', path: '/users/new', component: 'NewUser'},
  {name: 'user', path: '/users/:id', component: 'User', props: true},
  {name: 'group', path: '/groups/:id', component: 'Group', props: true},
  {name: 'notFound', path: '*', component: 'NotFound'}
]

const routes = routerOptions.map(route => {
  return {
    ...route,
    component: () => import(`@/views/${route.component}.vue`)
  }
})

Vue.use(Router)

export default new Router({
  routes: routes,
  mode: 'history'
})
