<template>
    <div>
      <user-detail v-bind:id="id"></user-detail>
    </div>
</template>

<script>
import UserDetail from '@/components/UserDetail.vue'

export default {
  name: 'User',
  props: ['id'],
  components: {
    UserDetail
  },
  created () {
    console.log(this.id)
  }
}
</script>

<style scoped>

</style>
