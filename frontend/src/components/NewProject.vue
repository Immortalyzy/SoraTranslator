<template>
    <div>
        <div class="new-project-title">
            <h1>WELCOME TO SORATRANSLATOR</h1>
            <button @click="openProject">Open Project</button>
        </div>
        <div v-if="displayIntro">
            <h2 class="new-project-title">CREATE A PROJECT</h2>
            <div class="new-project-instructions">
                <h3>Instructions:</h3>
                <p>You should at first analyse your game manually, then create a python file defining your game. It should
                    contains a Game class with the following functions:
                <ol>
                    <li>prepare_translation(): the function takes a folder path as parameter. It should create a
                        GameResrouces folder
                        as
                        described in the project's README.</li>
                    <li>integrate() (optional): the function takes a folder path as parameter. It should be able to put all
                        files from GameResroucesTree back to the Game. It will also update the TranslatedFiles folder so
                        that you can view the raw file with translated text. </li>
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
                    <label for="name">Project Name:</label>
                    <div class="input-area">
                        <input type="text" id="name" name="name" v-model="name">
                    </div>
                </div>
                <div class="option">
                    <label for="project_path">Project Path:</label>
                    <div class="input-area">
                        <input type="text" id="game_path" name="gameEngine" v-model="project_path">
                        <button @click="selectproject_path">...</button>
                    </div>
                </div>
                <div class="option">
                    <label for="game_path">Game Path:</label>
                    <div class="input-area">
                        <input type="text" id="game_path" name="gameEngine" v-model="game_path">
                        <button @click="selectGamePath">...</button>
                    </div>
                </div>
                <!--
                <div class="option">
                    <label for="gameEngine">Game Engine:</label>
                    <div class="input-area">
                        <input type="text" id="gameEngine" name="gameEngine" v-model="gameEngine">
                    </div>
                </div>-->
                <div class="option">
                    <label for="translator">Translator:</label>
                    <div class="input-area">
                        <input type="text" id="translator" name="translator" v-model="translator">
                    </div>
                </div>
                <div class="option">
                    <label for="Language">Language:</label>
                    <div class="input-area">
                        <input class="half-input" type="text" id="original_language" name="original_language"
                            v-model="original_language">
                        >
                        <input class="half-input" type="text" id="target_language" name="target_language"
                            v-model="target_language">
                    </div>
                </div>
            </div>
            <div>{{ this.projectTest.project_path }}</div>
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
            name: "Default",
            project_path: "~",
            game_path: "",
            translator: "gpt-3.5-16k",
            original_language: "Japanese",
            target_language: "Chinese (Simplified)",

            // for page display
            displayIntro: true,
            selectingWhich: "project_path"

        };
    },
    created() {
        window.electron.ipcRenderer.on("selected-path", (targetPath) => {
            // this method from chatgpt is a bit strange, but it allows the program to be interactive while the dialog is open
            console.log("Selected Path", targetPath);
            if (this.selectingWhich === "project_path") {
                this.project_path = targetPath;
            } else if (this.selectingWhich === "game_path") {
                this.game_path = targetPath;
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
        async openProject() {
            // open a window of selecting local files
            const project_file_path = await window.electron.ipcRenderer.invoke("select-file-dialog");
            // create post request to open the project
            const post_data = {
                project_file_path: project_file_path,
            };
            console.log(post_data);
            const http = axios.create({
                baseURL: "http://localhost:5000",
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                },
            });
            http.post("/open_project", post_data).then((response) => {
                console.log(response.data);
                const project = response.data;
                this.updateProject(project);
                alert("Project opened successfully.");
            }).catch((error) => {
                console.log(error);
            })
        },
        clickNext() {
            this.displayIntro = false;
        },
        createProject() {
            // add code to verify the data
            const project = this.$data;
            if (project.name === "") {
                alert("Please enter a project name.");
                return;
            }
            if (project.project_path === "") {
                alert("Please enter a project path.");
                return;
            }
            if (project.game_path === "") {
                alert("Please enter a game path.");
                return;
            }

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
            this.updateProject(project);

            this.$emit("change-display", "initialize_game")

        },
        selectproject_path() {
            window.electron.ipcRenderer.send("open-directory-dialog");
            this.selectingWhich = "project_path";
        },
        selectGamePath() {
            window.electron.ipcRenderer.send("open-file-dialog");
            this.selectingWhich = "game_path";
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
