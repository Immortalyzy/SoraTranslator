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
            <hr />
            <button @click="translateAll">Translate and save all files</button>
            <hr />
            <button @click="translateThis"> Translate this file</button>
            <br>
            <div class="actions-sub">
                <button> load </button>
                <button> save </button>
            </div>
        </div>
        <div class="information">
            <div v-for="(value, key) in currentInfo" :key="key" class="info-row">
                <div class="property-name">{{ key }}</div>
                <div class="property-value">{{ value }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex';
import axios from 'axios';
import { EventBus } from '@/utils/eventBus'
export default {
    name: 'ActionInfo',
    data() {
        return {
            temperature: 0.25,
            max_lines: 50
        }

    },
    methods: {
        translateAll() {
            // open a window of selecting local files
            alert("Not implemented yet");
        },
        translateThis() {
            // create the request
            let requestT = {};
            requestT["temperature"] = this.temperature;
            requestT["max_lines"] = this.max_lines;
            requestT["file_path"] = this.$store.getters.getCurrentDisplay["filePath"];
            console.log("Trying to translate : " + requestT["file_path"]);
            if (requestT["file_path"] == undefined) {
                alert("Please select a file first");
                return;
            }
            // if file path doesn't end with .csv, then it's not a csv file
            if (!requestT["file_path"].endsWith(".csv")) {
                alert("Please select a text rather than a script file");
                return;
            }
            const http = axios.create({
                baseURL: "http://localhost:5000",
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                },
            });

            // send the request
            http.post("http://localhost:5000/translate_text", requestT)
                .then(response => {
                    if (response.data["status"] == true) {
                        // if still displaying the same file, update manually the content
                        if (this.$store.state.currentDisplay["filePath"] == requestT["file_path"]) {
                            EventBus.emit("updateFileContent");
                        }

                        // and info
                    } else {
                        alert("Failed to translate the file" + response.data["file_path"]);

                    }
                });


            // update directory tree to display tranlsation status


        },
        save_file() {
        },
        load_file() {
            EventBus.emit("updateFileContent");
        },
        updateInfo() {
            // update the info based on last clicked item
            // if a file

            //todo: add other options when possible
        },

    },
    computed: {
        ...mapState({
            currentInfo: state => state.currentInfo
        })
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
