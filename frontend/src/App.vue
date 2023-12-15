<template>
  <div id="app">
    <div class="container">
      <DirectoryTree @file-selected="displayFile" />
      <FileDisplay :text="fileContent" />
    </div>
    <StatusBar :message="statusMessage" />
  </div>
</template>

<script>
import DirectoryTree from './components/DirectoryTree.vue';
import FileDisplay from './components/FileDisplay.vue';
import StatusBar from './components/StatusBar.vue';

export default {
  name: 'App',
  components: {
    DirectoryTree,
    FileDisplay,
    StatusBar
  },
  data() {
    return {
      fileContent: 'DISPLAY OF TEXT',
      statusMessage: 'STATUS'
    };
  },
  methods: {
    displayFile(content) {
      this.fileContent = content;
      this.statusMessage = 'Displaying content...';
    }
  }
};
</script>

<style>
.container {
  display: flex;
  height: 80vh;
}
</style>
