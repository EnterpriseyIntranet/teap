<template>
  <div id="app">
    <nav>
      <router-link :to="{name: 'home'}"><img src="./assets/logo.png" class="d-inline-block align-top logo" alt=""></router-link>
    </nav>
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<style>
.logo {
  width: 1em;
  height: auto;
}
</style>
