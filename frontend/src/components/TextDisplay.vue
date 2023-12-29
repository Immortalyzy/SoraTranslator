<template>
    <div class="grid">
        <ag-grid-vue :rowData="rowData" :columnDefs="colDefs" class="ag-theme-balham-dark" @grid-ready="onGridReady">
        </ag-grid-vue>
    </div>
</template>

<script>
import { ref } from 'vue';
import "ag-grid-community/styles/ag-grid.css"; // Core CSS
import "ag-grid-community/styles/ag-theme-balham.css"; // Theme
import { AgGridVue } from "ag-grid-vue3"; // Vue Grid Logic
import { readTextFile } from '@/utils/fileManagement'

export default {
    name: "App",
    components: {
        AgGridVue, // Add AG Grid Vue3 component
    },
    props: {
        filePath: {
            type: String,
            default: ""
        },
    },
    data() {
        return {
            blocks: [],
            rowData: [],
            gridApi: null,
        }

    },
    methods: {
        onGridReady(params) {
            this.gridApi = params.api;
            // Load your data here
            console.log("grid ready")
        },
        async getFileContent() {
            // clear the rowData
            if (this.filePath === "")
                return;
            // clear rowData
            this.rowData = [];
            this.blocks = [];
            const fileJson = await readTextFile(this.filePath);
            if (fileJson["status"] === true) {
                // Process your file data here
                const newBlocks = fileJson["blocks"].map(block => ({
                    name: block.name,
                    speaker_original: block.speaker_original,
                    text_original: block.text_original,
                    speaker_translated: block.speaker_translated,
                    text_translated: block.text_translated,
                }));

                // Update rowData with a new array to ensure reactivity
                this.rowData = [...newBlocks];

                // ! this is not necessary
                // Refresh the grid if the Grid API is ready
                //                if (this.gridApi) {
                //                    this.gridApi.refreshCells();
                //                }
            } else {
                console.error("Error reading file");
            }

        },

    },
    mounted() {
        this.rowData = [
            { name: "181", speaker_original: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！" },
            { name: "182", speaker_original: "瑠奈", text_original: "「決まってるじゃない、子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，" },
            { name: "183", speaker_original: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！" },
        ];
    },
    setup() {
        // colum definitions
        const colDefs = ref([
            { field: "name" },
            { field: "speaker_original" },
            { field: "text_original" },
            { field: "speaker_translated" },
            { field: "text_translated" },
        ]);

        return {
            colDefs,
        };

    },
    watch: {
        filePath: {
            handler: function () {
                this.getFileContent();
            },
            immediate: true
        }
    }
};
</script>

<style>
.grid {
    color: white;
    flex-basis: 100%;
}

.grid>* {
    height: calc(100vh - 55px - 70px - 7px);
}
</style>