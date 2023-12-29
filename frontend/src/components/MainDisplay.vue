<template>
  <div class="table-container">
    <div v-if="displayType === 'new_project'">
      <NewProject @change-display="changeDisplay" />
    </div>
    <div v-if="displayType === 'initialize_game'">
      <InitializeProject />
    </div>
    <div class="raw-text" v-if="isRaw">
      <div v-for="(line, index) in lines" :key="index" class="line">
        <span class="line-number">{{ index + 1 }}</span>
        <span class="line-content">{{ line }}</span>
      </div>
    </div>
    <div v-if="isText">
      <TextDisplay :filePath="filePath" />
    </div>
  </div>
</template>

<script>
import NewProject from "./NewProject.vue";
import InitializeProject from "./InitializeProject.vue";
import TextDisplay from "./TextDisplay.vue";
export default {
  name: "MainDisplay",
  components: {
    NewProject,
    InitializeProject,
    TextDisplay
  },
  props: {
    displayType: {
      type: String,
      default: "new_project"
    },
    filePath: {
      type: String,
      default: "DISPLAY OF TEXT"
    },
  },
  data() {
    return {
      fileContent: "DISAY OF TEXT",
      lines: [],
      isRaw: false,
      isText: false
    };
  },
  created() {
  },
  methods: {
    changeDisplay(type, filePath) {
      this.$emit("change-display", type, filePath)
    },
    async dispalyRaw() {
      console.log("displaying raw text at " + this.filePath)
      this.fileContent = await window.electron.ipcRenderer.invoke("read-file", this.filePath);
      this.lines = this.fileContent.split("\n");
    }
  },
  watch: {
    filePath: {
      handler: function () {
        if (this.displayType === "raw_text" || this.displayType === "translated_file" || this.displayType === "original_file") {
          console.log(this.displayType)
          this.dispalyRaw();
        }
      },
      immediate: true
    },
    displayType: {
      handler: function () {
        if (this.displayType === "raw_text" || this.displayType === "translated_file" || this.displayType === "original_file") {
          this.isRaw = true;
          this.isText = false;
        }
        if (this.displayType === "text") {
          this.isText = true;
          this.isRaw = false;
        }
      },
      immediate: true
    }
  }
};
</script>

<style>
.table-container>* {
  /* Adjust as needed */
  width: 100%;
  height: calc(100vh - 55px - 70px - 7px);
}

.raw-text {
  color: white;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: medium;
  font-weight: bold;
  padding: 0px 0px;
  margin: 0px 0px;
  flex-basis: calc(100% - 20px);
  overflow-y: auto;
  overflow-x: auto;
}

.line {
  display: flex;
}

.line-number {
  color: gray;
  text-align: right;
  width: 30px;
  margin: 0 5px;
}

.line-text {
  white-space: pre;
}
</style>
