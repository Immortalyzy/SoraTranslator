<template>
  <div class="container-directory-tree">
    <div class="title">
      {{ titleInfo }}
      <hr />
    </div>
    <div class="directory-tree" v-for="(value, name) in treeData" :key="name">
      <div class="folder-name">{{ name }}</div>
      <div class="folder-contents" v-if="isObject(value)">
        <tree-folder :tree-data="value" />
      </div>
      <div class="file-name" v-else>
        <h2>Please select a project.</h2>
      </div>
    </div>
  </div>
</template>

<script>
import { listFiles } from '../fileService.js'
import { ref, onMounted } from 'vue';
export default {
  name: "DirectoryTree",
  props: {
    currentTreeDisplay: {
      type: String,
      default: "S"
    },
  },
  data() {
    return {
      rawtextDirectory: this.$store.state.project.rawtext_directory,
      textDirectory: this.$store.state.project.text_directory,
      translatedFilesDirectory: this.$store.state.project.translated_files_directory,
    };
  },
  setup() {
    const files = ref([]);

    const toggle = (file) => {
      if (file.isDirectory) {
        file.isOpen = !file.isOpen;
      }
    };

    let path = "";
    if (this.currentTreeDisplay === "S") {
      path = this.rawtextDirectory;
    } else if (this.currentTreeDisplay === "T") {
      path = this.textDirectory;
    } else if (this.currentTreeDisplay === "R") {
      path = this.translatedFilesDirectory;
    }

    const loadFiles = async () => {
      files.value = await listFiles(path);
    };

    onMounted(loadFiles);

    return { files, toggle };
  },
  computed: {
    titleInfo() {
      if (this.currentTreeDisplay === "S") {
        return "Script Files:";
      } else if (this.currentTreeDisplay === "T") {
        return "Text Files:";
      } else if (this.currentTreeDisplay === "R") {
        return "Result Files:";
      }
      alert(this.currentTreeDisplay)
      return "Tree Display";
    }


  },
  methods: {
  }
};
</script>

<style>
.container-directory-tree {
  display: flex;
  flex-direction: column;
}

.title {
  color: white;
  font-size: large;
  font-weight: bold;
  flex-basis: 5%;
  align-items: center;
  vertical-align: middle;
  padding: 0 0;
  margin: 0px 0px;
}

.directory-tree {
  margin-left: 00px;
}

.folder-name {
  font-weight: bold;
}
</style>
