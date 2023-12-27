<template>
  <div class="table-container">
    <div v-if="displayType === 'new_project'">
      <NewProject />
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
export default {
  name: "FileDisplay",
  components: {
    NewProject
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
    };
  },
  methods: {
    editCell(rowIndex, cellIndex, event) {
      this.tableData[rowIndex][cellIndex] = event.target.innerText;
    },
  },
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

/* Additional styling as needed */
</style>
