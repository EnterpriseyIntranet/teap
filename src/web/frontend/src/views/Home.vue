<template>
  <div>
    <users></users>
    <groups></groups>
  </div>
</template>

<script>
import Users from '@/components/Users.vue'
import Groups from '@/components/Groups.vue'

export default {
  name: 'Home',
  components: {
    Users,
    Groups
  }
}
</script>
