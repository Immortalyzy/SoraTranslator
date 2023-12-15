<template>
  <div class="status-bar">
    {{ message }}
  </div>
</template>

<script>
export default {
  name: 'StatusBar',
  props: {
    message: String
  }
};
</script>

<style scoped>
.status-bar {
  background-color: #222;
  color: #fff;
  padding: 10px;
  text-align: center;
}
</style>
