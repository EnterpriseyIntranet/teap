<template>
  <div>
    <franchises></franchises>
    <create-franchise></create-franchise>
  </div>
</template>

<script>
import Franchises from '@/components/Franchises.vue'
import CreateFranchise from '@/components/CreateFranchise.vue'

export default {
  name: 'FranchisesView',
  components: {
    Franchises,
    CreateFranchise
  }
}
</script>
