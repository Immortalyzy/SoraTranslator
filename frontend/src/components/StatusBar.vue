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
  padding: 0 0;
  margin: 0px 0px;
  text-align: left;
}
</style>
