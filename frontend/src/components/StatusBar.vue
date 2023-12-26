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
  background-color: rgba(34, 34, 34, 0.233);
  color: #fff;
  padding: 10px;
  text-align: left;
}
</style>
