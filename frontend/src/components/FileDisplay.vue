<template>
  <div class="table-container">
    <div v-if="displayType === 'new_project'">
      <NewProject @change-display="changeDisplay" />
    </div>
    <div v-if="displayType === 'initialize_game'">
      <InitializeProject />
    </div>
    <div class="raw-text" v-if="displayType === 'raw_text'">
      <div v-for="(line, index) in lines" :key="index" class="line">
        <span class="line-number">{{ index + 1 }}</span>
        <span class="line-content">{{ line }}</span>
      </div>
    </div>
    <table v-if="displayType === 'TextFile'">
      <thead>
        <tr>
          <th v-for="header in headers" :key="header">{{ header }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, rowIndex) in tableData" :key="rowIndex">
          <td v-for="(cell, cellIndex) in row" :key="cellIndex" contenteditable
            @blur="editCell(rowIndex, cellIndex, $event)">
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import NewProject from "./NewProject.vue";
import InitializeProject from "./InitializeProject.vue";
export default {
  name: "FileDisplay",
  components: {
    NewProject,
    InitializeProject
  },
  props: {
    displayType: {
      type: String,
      default: "new_project"
    },
    filePath: {
      type: String,
      default: "DISPLAY OF TEXT"
    }
  },
  data() {
    return {
      headers: ['Name', 'Age', 'Occupation'],
      tableData: [
        ['Alice', 28, 'Engineer'],
        ['Bob', 34, 'Designer'],
        // ... more rows
      ],
      fileContent: "DISAY OF TEXT",
      lines: [],
    };
  },
  created() {
  },
  methods: {
    editCell(rowIndex, cellIndex, event) {
      this.tableData[rowIndex][cellIndex] = event.target.innerText;
    },
    changeDisplay(type, filePath) {
      this.$emit("change-display", type, filePath)
    },
    async dispalyRaw() {
      if (this.displayType === "raw_text" || this.displayType === "text" || this.displayType === "translated_file") {
        this.fileContent = await window.electron.ipcRenderer.invoke("read-file", this.filePath);
        this.lines = this.fileContent.split("\n");
      }

    }
  },
  watch: {
    filePath: {
      handler: function () {
        if (this.displayType === "raw_text" || this.displayType === "text" || this.displayType === "translated_file") {
          console.log(this.displayType)
          this.dispalyRaw();
        }
      },
      immediate: true
    }
  }
};
</script>

<style>
.table-container {
  overflow: auto;
  /* Adjust as needed */
  width: 70%;
}

table {
  width: 100%;
  border-collapse: collapse;
  color: white;
}

th,
td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
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
