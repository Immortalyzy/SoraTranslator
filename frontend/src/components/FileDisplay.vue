<template>
  <div class="file-display">
    <pre>{{ text }}</pre>
    <div class="actions">
      <button>Edit</button>
      <button>Delete</button>
      <button>Save</button>
      <!-- Add more buttons as needed -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'FileDisplay',
  props: {
    text: String
  }
};
</script>

<style scoped>
.file-display {
  flex: 3;
  background-color: #fff;
  padding: 10px;
  overflow-y: auto;
}

.actions {
  margin-top: 10px;
}

button {
  margin-right: 5px;
}
</style>
