<template>
    <div>
      <group-detail v-bind:id="id"></group-detail>
    </div>
</template>

<script>
import GroupDetail from '@/components/GroupDetail.vue'

export default {
  name: 'User',
  props: ['id'],
  components: {
    GroupDetail
  }
}
</script>

<style scoped>

</style>
