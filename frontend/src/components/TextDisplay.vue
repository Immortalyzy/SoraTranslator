<template>
    <div class="hot-table">
        <hot-table ref="hotInstance" :data="rowData" :settings="hotSettings">
        </hot-table>
    </div>
</template>

<script>
import { defineComponent } from 'vue';
import { HotTable } from '@handsontable/vue3';
import { registerAllModules } from 'handsontable/registry';
import 'handsontable/dist/handsontable.full.css';
import { readTextFile } from '@/utils/fileManagement'
import { EventBus } from '@/utils/eventBus'

registerAllModules();

export default defineComponent({
    name: "App",
    components: {
        HotTable,
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
            rowData: [
                { name: "181", speakerOriginal: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speakerTranslated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！" },
                { name: "181", speakerOriginal: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speakerTranslated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！" },
                { name: "182", speakerOriginal: "瑠奈", text_original: "「決まってるじゃない、子の正体を暴くのよ！」", speakerTranslated: "", text_translated: "「你不是知道吗，" },
                { name: "183", speakerOriginal: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speakerTranslated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！" },
            ],
            hotSettings: {
                width: '100%',
                height: '100%',
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation',
                colHeaders: ["name", "Sp_O", "Original Text", "Sp_T", "Translated Text"],
                columns: [
                    { data: "name", readOnly: true },
                    { data: "speakerOriginal", readOnly: true },
                    { data: "text_original", readOnly: true },
                    { data: "speakerTranslated", readOnly: false },
                    { data: "text_translated", readOnly: false },
                ],
                manualColumnResize: true,
                manualColumnMove: true,
                cells: function (row) {
                    var cellProperties = {};
                    if (row % 2 === 0) {
                        cellProperties.className = 'alternateRow';
                    }
                    return cellProperties;
                },
            },
            cNameSettings: {
                manualColumnResize: true,
            }
        }

    },
    mounted() {
        EventBus.on("updateFileContent", this.getFileContent);
        const hotInstance = this.$refs.hotInstance.hotInstance;
        return {
            hotInstance
        }
    },
    unmounted() {
        EventBus.off("updateFileContent", this.getFileContent);
    },
    methods: {
        async getFileContent() {
            // clear the rowData
            if (this.filePath === "")
                return;
            // clear rowData
            //            this.rowData = [];
            this.blocks = [];
            const fileJson = await readTextFile(this.filePath);
            if (fileJson["status"] === true) {
                // Process your file data here
                const newBlocks = fileJson["blocks"].map(block => ({
                    name: block.name,
                    speakerOriginal: block.speaker_original,
                    text_original: block.text_original,
                    speakerTranslated: block.speaker_translated,
                    text_translated: block.text_translated,
                }));

                // Update rowData with a new array to ensure reactivity
                this.rowData = [...newBlocks];
                // update the table
                console.log(this.rowData);
                this.$refs.hotInstance.hotInstance.updateData(newBlocks);
            } else {
                console.error("Error reading file");
            }

        },
        getEditedData() {
            const hotInstance = this.$refs.hotInstance.hotInstance;
            const editedData = hotInstance.getSourceData();
            console.log(editedData);
            return editedData;
        },

    },
    watch: {
        filePath: {
            handler: function () {
                this.getFileContent();
            },
            immediate: true
        }
    }
});
</script>

<style>
.hot-table {
    height: calc(100vh - 55px - 70px - 7px);
    background-color: transparent;
    opacity: 0.8;
}

.hot-table>* {
    width: 100%;
    height: calc(100vh - 55px - 70px - 7px);
    background-color: transparent;
}


.ht_master tr:nth-of-type(even)>td {
    background-color: rgb(120, 50, 50);
}

.ht_master tr:nth-of-type(odd)>td {
    background-color: rgb(120, 120, 55);
}

.handsontable {
    color: white;
}
</style>