<template>
  <div id="app">
    <nav>
      <img src="./assets/logo.png" class="d-inline-block align-top logo" alt="">
      <router-link to="/">Home</router-link>
    </nav>
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
.logo {
  width: 1em;
  height: auto;
}
</style>
