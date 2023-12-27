<template>
    <div>
        <div class="new-project-title">
            <h1>WELCOME TO SORATRANSLATOR</h1>
            <h2>CREATE A PROJECT</h2>
        </div>
        <div v-if="displayIntro">
            <div class="new-project-instructions">
                <h3>Instructions:</h3>
                <p>You should at first analyse your game manually, then create a python file defining your game. It should
                    contains the following functions:
                <ol>
                    <li>intialize(): the function takes a folder path as parameter. It should create a GameResrouces folder
                        as
                        described in the project's README.</li>
                    <li>integrate() (optional): the function takes a folder path as parameter. It should be about to put all
                        files from GameResroucesTree back to the Game. </li>
                </ol>
                This translator provides several built-in integrators (for Chaos-R games), in that case you can simple give
                a path to the game folder. Note that the integrator will modify the original game, so always KEEP A BACKUP.
                <br>
                <br>
                Save the path to this python file and click "Next".
                </p>
            </div>
            <button @click="clickNext">Next</button>
        </div>
        <div v-else>
            <div class="option-container">
                <div class="option">
                    <label for="projectName">Project Name:</label>
                    <div class="input-area">
                        <input type="text" id="projectName" name="projectName" v-model="projectName">
                    </div>
                </div>
                <div class="option">
                    <label for="projectPath">Project Path:</label>
                    <div class="input-area">
                        <input type="text" id="gamePath" name="gameEngine" v-model="projectPath">
                        <button @click="selectProjectPath">...</button>
                    </div>
                </div>
                <div class="option">
                    <label for="gamePath">Game Path:</label>
                    <div class="input-area">
                        <input type="text" id="gamePath" name="gameEngine" v-model="gamePath">
                        <button @click="selectGamePath">...</button>
                    </div>
                </div>
                <div class="option">
                    <label for="gameEngine">Game Engine:</label>
                    <div class="input-area">
                        <input type="text" id="gameEngine" name="gameEngine" v-model="gameEngine">
                    </div>
                </div>
                <div class="option">
                    <label for="translator">Translator:</label>
                    <div class="input-area">
                        <input type="text" id="translator" name="translator" v-model="translator">
                    </div>
                </div>
                <div class="option">
                    <label for="Language">Language:</label>
                    <div class="input-area">
                        <input class="half-input" type="text" id="fromLanguage" name="fromLanguage" v-model="fromLanguage">
                        >
                        <input class="half-input" type="text" id="toLanguage" name="toLanguage" v-model="toLanguage">
                    </div>
                </div>
            </div>
            <div>{{ this.projectTest.projectPath }}</div>
            <button @click="createProject">Create</button>
            <div>
            </div>
        </div>
    </div>
</template>

<script>
import { useStore } from 'vuex'
import axios from 'axios'
import { computed } from 'vue'
export default {
    name: "NewProject",
    props: {
    },
    data() {
        return {
            // for new project
            projectName: "Default",
            projectPath: "~",
            gamePath: "",
            translator: "gpt-3.5-16k",
            fromLanguage: "Japanese",
            toLanguage: "Chinese (Simplified)",

            // for page display
            displayIntro: true,
            selectingWhich: "projectPath"

        };
    },
    created() {
        window.electron.ipcRenderer.on("selected-path", (path) => {
            // this method from chatgpt is a bit strange, but it allows the program to be interactive while the dialog is open
            console.log("Selected Path", path);
            if (this.selectingWhich === "projectPath") {
                this.projectPath = path;
            } else if (this.selectingWhich === "gamePath") {
                this.gamePath = path;
            }
        });
    },
    setup() {
        const store = useStore();
        const updateProject = (project) => {
            store.dispatch("updateProject", project);
        };
        const projectTest = computed(() => store.state.project);
        return { updateProject, projectTest };

    },
    methods: {
        clickNext() {
            this.displayIntro = false;
        },
        createProject() {
            alert("Project created!");
            // add code to verify the data
            const project = this.$data;

            // add code to create the project object using python, and save to the destination path
            const http = axios.create({
                baseURL: "http://localhost:5000",
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                },
            });
            http.post("/create_project", project).then((response) => {
                console.log(response.data);
            }).catch((error) => {
                console.log(error);
            })
            // if success, then update the project
            // if (response.data.result["success"] === true) { updateProject(project); }
            // if failed, then alert the user
            // if (response.data.result["success"] === false) { alert("Project creation failed. Please check the path."); }
            this.updateProject(project);

        },
        selectProjectPath() {
            window.electron.ipcRenderer.send("open-directory-dialog");
            this.selectingWhich = "projectPath";
        },
        selectGamePath() {
            window.electron.ipcRenderer.send("open-file-dialog");
            this.selectingWhich = "gamePath";
        },
        changeGamePath(path) {
            const file = path.target.files[0];
            if (file) {
                this.gamePath = file.name;
            }
        },
    },
    beforeUnmount() {
        window.electron.ipcRenderer.removeAllListeners("selected-path");
    },
};
</script>

<style>
/* For new project */
.new-project-title {
    color: white;
    font-size: large;
    text-align: center;
    font-weight: bold;
    text-align: center;
}

.new-project-instructions {
    color: white;
    font-size: 20px;
    text-align: left;
    font-weight: bold;
}

button {
    margin: 0px 5px;
    padding: 5px 20px;
    font-size: large;
    align-items: center;
    display: inline-block;
    border: 1px solid #ffd0d0;
    background-color: rgb(179, 116, 0);
    color: rgb(255, 255, 255);
    text-align: center;
    text-decoration: none;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
    /* Red glow */
}

.option-container {
    display: flex;
    margin: 0 10%;
    flex-direction: column;
    align-items: left;
    text-align: left;
    border: white;
}

.option-container>* {
    height: 30px;
    font-size: 25px;
    text-align: left;
}


.option {
    display: flex;
    flex-direction: row;
    color: white;
    flex-basis: 5%;
}

label {
    display: inline-block;
    color: rgb(255, 255, 255);
    width: 200px;
    flex-shrink: 0;
    flex-grow: 0;
    text-align: right;
}

.input-area {
    display: flex;
    flex-direction: row;
    align-items: left;
    justify-items: normal;
    width: calc(100% - 200px);
}

input {
    font-size: 25px;
    color: rgb(255, 255, 255);
    background-color: rgba(0, 0, 0, 0.295);
    border: 1px solid #ffd0d0;
    border-radius: 5px;
    flex-shrink: 0;
    flex-grow: 0;
    text-align: left;
}

.half-input {
    /*    width: 200px; */
    flex-shrink: 0;
    flex-grow: 0;
    text-align: left;
}
</style>
