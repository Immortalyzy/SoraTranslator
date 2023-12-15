<template>
  <div class="directory-tree">
    <button v-for="dir in directories" :key="dir.name" @click="selectFile(dir)">
      {{ dir.name }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'DirectoryTree',
  data() {
    return {
      directories: [
        { name: 'B1', content: 'Content of B1' },
        { name: 'B2', content: 'Content of B2' },
        // ... other directories
      ]
    };
  },
  methods: {
    selectFile(dir) {
      this.$emit('file-selected', dir.content);
    }
  }
};
</script>

<style scoped>
.directory-tree {
  flex: 1;
  background-color: #f0f0f0;
  padding: 10px;
}

button {
  display: block;
  margin: 5px 0;
  padding: 5px;
}
</style>
