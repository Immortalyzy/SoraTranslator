<template>
    <div class="action-info-block">
        <div class="actions">
            <hr />
            <div class="action-settings-title">Temp translation settings</div>
            <div class="action-sub">
                <label>Temperature: </label>
                <input type="text" placeholder="0.25" v-model="temperature" />
            </div>
            <div class="action-sub">
                <label>Maximum lines: </label>
                <input type="text" placeholder="50" v-model="max_lines" />
            </div>
            <div class="action-sub">
                <label>Separation: </label>
                <input type="text" placeholder="50" v-model="separation_method" />
            </div>
            <div class="action-sub">
                <label>Joiner: </label>
                <input type="text" placeholder="50" v-model="joiner" />
            </div>
            <hr />
            <button @click="translateAll">Translate all files</button>
            <button @click="stop">Stop</button>
            <hr />
            <button @click="translateThis"> Translate this file</button>
            <hr />
            <div class="actions-sub">
                <button @click="loadFile"> load </button>
                <button @click="saveFile"> save </button>
            </div>
            <hr />
            <button @click="markFixed"> Mark as fixed </button>
            <button @click="markUntranslated"> Mark as untranslated </button>
        </div>
        <div class="information">
            <div v-for="(value, key) in currentInfo" :key="key" class="info-row">
                <div class="property-name">{{ key }}: </div>
                <div class="property-value">{{ value }}</div>
                <hr />
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';
import { EventBus } from '@/utils/eventBus'
import { translateFile, changeFileProperty, translateAllFiles } from '@/utils/fileManagement'
import { requestFileInfo } from '@/utils/info';
export default {
    name: 'ActionInfo',
    data() {
        return {
            temperature: 0.25,
            max_lines: 50,
            separation_method: "[]",
            joiner: "|",
        }

    },
    methods: {
        async translateAll() {
            // TODO: properly set the translator at program initiation
            // get the current translator, temp solution,
            const response = await axios.get('http://localhost:5000/preferences');
            this.$store.state.currentTranslator = response.data["translator"]
            alert("Translator set to: " + this.$store.state.currentTranslator);
            translateAllFiles(this.temperature, this.max_lines);
        },
        stop() {
            if (this.$store.state.currentTranslation.translating) {
                alert("Stop signal sent, please wait for the current file to finish translation.");
                this.$store.state.stopSignal = true;
            }
        },
        translateThis() {
            let toTranslateFilePath = this.$store.getters.getCurrentDisplay["filePath"];
            translateFile(toTranslateFilePath, this.temperature, this.max_lines);
        },
        saveFile() {
            EventBus.emit("saveFile");
        },
        loadFile() {
            EventBus.emit("updateFileContent");
        },
        async markFixed() {
            let changeRequest = {};
            changeRequest.file_path = this.$store.getters.getCurrentDisplay["filePath"];
            changeRequest.property_name = "need_manual_fix";
            changeRequest.property_value = false;
            await changeFileProperty(changeRequest);
            EventBus.emit("updateTranslationStatus");
        },
        async markUntranslated() {
            let changeRequest = {};
            changeRequest.file_path = this.$store.getters.getCurrentDisplay["filePath"];
            changeRequest.property_name = "is_translated";
            changeRequest.property_value = false;
            await changeFileProperty(changeRequest);
            EventBus.emit("updateTranslationStatus");

        },
        updateInfo() {
            // update the info based on last clicked item
            // if a file
            requestFileInfo();

            //todo: add other options when possible
        },

    },
    computed: {
        ...mapState({
            currentInfo: state => state.currentInfo
        })
    },
    mounted() {
        EventBus.on("updateInfo", this.updateInfo);
    },
    unmounted() {
        EventBus.off("updateInfo", this.updateInfo);
    }

};
</script>

<style scoped>
.action-info-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0 0;
}

.action-info-block>* {
    margin: 0 0;
    padding: 0 0;
    width: 100%;
}

.actions {
    margin: 0px 0px;
    height: 50%;
    border: #ffd0d0;
    align-items: center;
    overflow: auto;
}

.action-settings-title {
    color: white;
    text-align: center;
    font-size: 25px;
}

.actions-sub {
    display: flex;
    width: 100%;
    flex-direction: row;
}

.actions-sub>* {
    width: 43%;
    margin: 5px 5px;
    padding: 5px 20px;
    align-items: center;
}

label {
    width: 50%;
    text-align: right;
    font-size: large;
    display: inline-block;
    color: white;
    border: white;
}

input {
    width: 40%;
    margin: 2px 5px;
    text-align: left;
    font-size: large;
    display: inline-block;
    background-color: rgba(97, 27, 27, 0.226);
    color: white;
    border: white;
    border-radius: 1px;
    flex-shrink: 0;
    flex-grow: 0;
}


button {
    width: 90%;
    margin: 5px 5px;
    padding: 5px 10px;
    font-size: large;
    border: 1px solid #ffd0d0;
    background-color: rgb(179, 116, 0);
    color: rgb(255, 255, 255);
    text-align: center;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
    /* Red glow */
}

button :hover {
    background-color: rgb(255, 255, 255);
    color: rgb(179, 116, 0);
    border-color: rgb(179, 116, 0);
}

.information {
    display: flex;
    flex-direction: column;
    margin: 0px 0px;
    padding: 0px 0px;
    font-size: large;
    border: 1px solid #ffd0d0;
    color: rgb(255, 255, 255);
    text-decoration: none;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
    /* Red glow */
    height: 50%;
    overflow-y: auto;
}

.info-row {
    display: flex;
    flex-direction: row;
    margin-bottom: 10px;
}

.property-name {
    width: 30%;
    flex-shrink: 0;
    flex-grow: 0;
    flex-basis: 30%;
    font-weight: bold;

    text-align: right;
    margin-right: 5px;
    display: inline-block;
    /* Add more styles for property name */
}

.property-value {
    width: 70%;
    flex-basis: 70%;
    text-align: left;
    display: inline-block;
    /* Add more styles for property value */
}
</style>
