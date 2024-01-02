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
import { readTextFile, saveTextFile } from '@/utils/fileManagement'
import { EventBus } from '@/utils/eventBus'

registerAllModules();
function cellClasses(row) {
    let classes = [];
    classes.push('normal-text');
    if (row % 2 === 0) {
        classes.push('alternateRow');
    }
    return classes.join(' ');
}

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
                { name: "181", speaker_original: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！", is_edited: false },
                { name: "181", speaker_original: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！", is_edited: false },
                { name: "182", speaker_original: "瑠奈", text_original: "「決まってるじゃない、子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，", is_edited: false },
                { name: "183", speaker_original: "玲奈", text_original: "「決まってるじゃない、昨日の女の子の正体を暴くのよ！」", speaker_translated: "", text_translated: "「你不是知道吗，就是要揭开昨天那个女孩的真正身份！", is_edited: false },
            ],
            specialRows: [],
            hotSettings: {
                width: '100%',
                height: '100%',
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation',
                colHeaders: ["name", "Sp_O", "Original Text", "Sp_T", "Translated Text"],
                wordWrap: true,
                columns: [
                    { data: "name", readOnly: true },
                    { data: "speaker_original", readOnly: true },
                    { data: "text_original", readOnly: true },
                    { data: "speaker_translated", readOnly: false },
                    { data: "text_translated", readOnly: false },
                ],
                manualColumnResize: true,
                manualColumnMove: true,
                cells: function (row) {
                    var cellProperties = {};
                    cellProperties.className = cellClasses(row);
                    //                    if (this.rowData && this.rowData[row]) {
                    //                        // Check if the row is edited and apply the 'edited-row' class
                    //                        if (this.rowData[row].is_edited) {
                    //                            cellProperties.className = cellProperties.className + " edited-row";
                    //                        }
                    //                   }
                    return cellProperties;
                },
                afterChange: (changes, source) => {
                    if (source !== 'loadData' && changes) {
                        changes.forEach(([row, oldValue, newValue]) => {
                            if (oldValue !== newValue) {
                                this.rowData[row].is_edited = true;
                            }
                        });
                    }
                },
            },
            cNameSettings: {
                manualColumnResize: true,
            }
        }

    },
    mounted() {
        EventBus.on("updateFileContent", this.getFileContent);
        EventBus.on("saveFile", this.saveFile);
        window.addEventListener('resize', this.updateHotSettings);
        this.updateHotSettings();
        const hotInstance = this.$refs.hotInstance.hotInstance;
        return {
            hotInstance
        }
    },
    unmounted() {
        EventBus.off("updateFileContent", this.getFileContent);
        EventBus.on("saveFile", this.saveFile);
        window.removeEventListener('resize', this.updateHotSettings);
    },
    methods: {
        //        isVerticalScrollbarPresent() {
        //            const hotContainer = this.$refs.hotInstance.$el;
        //            if (!hotContainer) {
        //                console.error("Handsontable container not found");
        //                return false;
        //            }
        //
        //            const htCore = hotContainer.querySelector('.htCore');
        //            if (!htCore) {
        //                console.error("Handsontable core element not found");
        //                return false;
        //            }
        //            // todo this is not working
        //            return hotContainer.offsetWidth > htCore.clientWidth;
        //        },
        calculateColumnWidths() {
            const containerElement = this.$refs.hotInstance.$el;
            if (!containerElement) {
                console.error("Container element not found");
                return []; // Return an empty array to use default widths
            }

            const scrollbarWidth = 17; //this.isVerticalScrollbarPresent() ? 17 : 17; // Adjust scrollbar width if needed
            const containerWidth = containerElement.offsetWidth - scrollbarWidth;
            const ratio = [5, 10, 40, 10, 35]; // Your specified ratios
            const totalRatio = ratio.reduce((a, b) => a + b, 0);
            return ratio.map(w => (w / totalRatio) * containerWidth);
        },

        updateHotSettings() {
            this.hotSettings = Object.assign({}, this.hotSettings, {
                colWidths: this.calculateColumnWidths()
            });
            // this.hotSettings = {
            //     ...this.hotSettings,
            //     colWidths: this.calculateColumnWidths(),
            // };
        },
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
                    speaker_original: block.speaker_original,
                    text_original: block.text_original,
                    speaker_translated: block.speaker_translated,
                    text_translated: block.text_translated,
                    is_edited: false,
                }));

                // Update rowData with a new array to ensure reactivity
                this.rowData = [...newBlocks];
                this.$refs.hotInstance.hotInstance.updateData(newBlocks);
                this.updateHotSettings();
            } else {
                console.error("Error reading file");
            }

        },
        saveFile() {
            let fileToSave = {
                "blocks": this.rowData,
                "filePath": this.filePath
            }
            saveTextFile(fileToSave);
            return this.rowData;
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

.handsontable .htDimmed {
    color: white;
}

.hot-table>* {
    width: 100%;
    height: calc(100vh - 55px - 70px - 7px);
    background-color: transparent;
}

.normal-text {
    font-family: 'Microsoft YaHei', sans-serif;
    font-size: medium;
    text-align: left;
    padding: 0px 0px;
    margin: 0px 0px;
}

.edited-row {
    color: green !important;
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