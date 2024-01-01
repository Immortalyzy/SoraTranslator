<template>
  <div class="container-directory-tree">
    <div class="title">
      {{ titleInfo }}
    </div>
    <div class="file-list">
      <ul>
        <li v-for="file in      this.files     " :key="file.path" @click="clickItem(file.path)" :class="{
          'selected-item': selectedPath === file.path,
          'need-manual-fix': file.needManualFix,
          'not-translated': file.notTranslated,
          'translated': file.translated,
          'invalid-file': file.invaildFile
        }">
          {{ file.displayPath }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
// import { ipcRenderer } from 'electron'
import axios from 'axios';
import { EventBus } from '@/utils/eventBus'
import { mapState } from 'vuex';
import { mapActions } from 'vuex';
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
      selectedPath: null,
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
      } else if (this.currentTreeDisplay === "O") {
        return "Original Files:";
      }
      return "Tree Display";
    },
    ...mapState({
      files: state => state.currentFileList,
    }),

  },
  methods: {
    ...mapActions({
      updateFileList: 'updateFileList',
    }),
    async loadDirectory() {
      const rawtextDirectory = this.$store.getters.getProject.rawtext_directory;
      const textDirectory = this.$store.getters.getProject.text_directory;
      const translatedFilesDirectory = this.$store.getters.getProject.translated_files_directory;
      const originalFilesDirectory = this.$store.getters.getProject.original_files_directory;
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
      } else if (this.currentTreeDisplay === "O") {
        tempTree = originalFilesDirectory;
      }
      console.log("Trying to display tree", tempTree)
      if (tempTree === "") {
        console.log("No directory to display");
        return;
      }
      let resultReturned = await window.electron.ipcRenderer.invoke("list-files", tempTree);
      console.log("Result Returned", resultReturned);
      //this.files = resultReturned;
      this.updateFileList(resultReturned);
      this.updateTranslationStatus();
    },
    clickItem(filePath) {
      let displayType = "text";
      if (this.currentTreeDisplay === "R") {
        displayType = "raw_text";
      } else if (this.currentTreeDisplay === "T") {
        displayType = "text";
      } else if (this.currentTreeDisplay === "F") {
        displayType = "translated_file";
      } else if (this.currentTreeDisplay === "O") {
        displayType = "original_file";
      }
      this.selectedPath = filePath;
      this.$emit("change-display", displayType, filePath);
    },
    updateTranslationStatus() {
      if (!(this.currentTreeDisplay === "T")) {
        return;
      }
      console.log("Updating translation status" + " for " + this.currentTreeDisplay);
      // create a list of file paths to check
      let pathsToCheck = [];
      for (let i = 0; i < this.files.length; i++) {
        pathsToCheck.push(this.files[i].path);
      }
      const requestT = { "file_paths": pathsToCheck };
      const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
          "Content-type": "application/json",
        },
      });

      // send the request
      http.post("http://localhost:5000/require_translation_status", requestT)
        .then(response => {
          if (response.data["status"] == true) {
            // update info for files
            for (let i = 0; i < this.files.length; i++) {
              this.files[i].needManualFix = response.data["status_list"][i] == "need_manual_fix";
              this.files[i].notTranslated = response.data["status_list"][i] == "not_translated";
              this.files[i].translated = response.data["status_list"][i] == "translated";
              this.files[i].invaildFile = response.data["status_list"][i] == "invalid_file";
            }
          } else {
            alert("Failed to load translation status, please check the text folder. It should not contain any files other than .csv files");
          }
        });

    },

  },
  mounted() {
    console.log("Mounted");
    EventBus.on("updateTranslationStatus", this.updateTranslationStatus);
    EventBus.on("loadDirectory", this.loadDirectory);
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

<style scoped>
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

.selected-item {
  background-color: brown;
  border: 1px solid rgb(171, 200, 0);
  /* Border color on hover */
  box-shadow: 0 0 10px rgba(0, 0, 255, 0.5);
  /* Glowing effect */
  /* Change cursor to indicate it's clickable or interactive */
}

.not-translated {
  color: rgb(255, 255, 255);
}

.need-manual-fix {
  color: rgb(255, 255, 0);
}

.translated {
  color: rgb(0, 255, 0);
}

.invalid-file {
  color: rgb(255, 0, 0);
}
</style>
