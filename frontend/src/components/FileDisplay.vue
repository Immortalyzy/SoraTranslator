<template>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th v-for="header in headers" :key="header">{{ header }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, rowIndex) in tableData" :key="rowIndex">
          <td v-for="(cell, cellIndex) in row" :key="cellIndex" contenteditable @blur="editCell(rowIndex, cellIndex, $event)">
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
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
  max-height: 300px; /* Adjust as needed */
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

/* Additional styling as needed */
</style>
