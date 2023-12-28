<template>
  <div class="container-directory-tree">
    <div class="title">
      {{ titleInfo }}
    </div>
    <div class="file-list">
      <ul>
        <li v-for="file in this.files" :key="file.path" @click="clickItem(file.path)">
          {{ file.displayPath }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
// import { ipcRenderer } from 'electron'
export default {
  name: "DirectoryTree",
  props: {
    currentTreeDisplay: {
      type: String,
      default: "R"
    },
  },
  data() {
    return {
      files: null,
    };
  },
  setup() {
  },
  computed: {
    titleInfo() {
      if (this.currentTreeDisplay === "R") {
        return "Raw Text Files:";
      } else if (this.currentTreeDisplay === "T") {
        return "Text Files:";
      } else if (this.currentTreeDisplay === "F") {
        return "Result Files:";
      }
      return "Tree Display";
    },

  },
  methods: {
    async loadDirectory() {
      const rawtextDirectory = this.$store.getters.getProject.rawtext_directory;
      const textDirectory = this.$store.getters.getProject.text_directory;
      const translatedFilesDirectory = this.$store.getters.getProject.translated_files_directory;
      console.log("loading tree for")
      console.log(rawtextDirectory)
      console.log(textDirectory)
      console.log(translatedFilesDirectory)

      let tempTree = "";
      if (this.currentTreeDisplay === "R") {
        tempTree = rawtextDirectory;
      } else if (this.currentTreeDisplay === "T") {
        tempTree = textDirectory;
      } else if (this.currentTreeDisplay === "F") {
        tempTree = translatedFilesDirectory;
      }
      console.log("Trying to display tree", tempTree)
      if (tempTree === "") {
        console.log("No directory to display");
        return;
      }
      let resultReturned = await window.electron.ipcRenderer.invoke("list-files", tempTree);
      console.log("Result Returned", resultReturned);
      this.files = resultReturned;
    },
    clickItem(filePath) {
      let displayType = "text";
      if (this.currentTreeDisplay === "R") {
        displayType = "raw_text";
      } else if (this.currentTreeDisplay === "T") {
        displayType = "text";
      } else if (this.currentTreeDisplay === "F") {
        displayType = "translated_file";
      }
      this.$emit("change-display", displayType, filePath);
    },

  },
  mounted() {
    console.log("Mounted");
    this.loadDirectory();
  },
  // watch this.currentTreeDisplay
  watch: {
    currentTreeDisplay: {
      handler: function () {
        console.log("Tree display changed");
        this.loadDirectory();
      },
      immediate: true
    },
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
  align-items: center;
  vertical-align: middle;
  padding: 0 0;
  margin: 0px 0px;
  height: 20px;
}

.folder-name {
  font-weight: bold;
}

.file-list {
  color: white;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: medium;
  font-weight: bold;
  text-align: left;
  padding: 0px 0px;
  margin: 0px 0px;
  flex-basis: calc(100% - 20px);
  overflow-y: auto;
  overflow-x: auto;
}

.file-list ul {
  list-style-type: none;
  padding-left: 0;
}

.file-list ul li {
  white-space: nowrap;
  /* Prevents the text from wrapping */
  /* Enables horizontal scrolling */
  text-overflow: ellipsis;
  /* Optional: Adds an ellipsis if the text is too long */
  /* Additional styling as needed */
  border: 1px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;

}

.file-list ul li:hover {
  background-color: brown;
  border: 1px solid rgb(171, 200, 0);
  /* Border color on hover */
  box-shadow: 0 0 10px rgba(0, 0, 255, 0.5);
  /* Glowing effect */
  /* Change cursor to indicate it's clickable or interactive */
}
</style>
