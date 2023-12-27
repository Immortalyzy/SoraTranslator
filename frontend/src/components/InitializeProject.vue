<template>
    <div>
        <div class="new-project-title">
            <h1>WELCOME TO SORATRANSLATOR</h1>
            <h2>CREATE A PROJECT</h2>
        </div>
        <div class="new-project-instructions">
            <h3>Instructions:</h3>
            <p> Please check the following information are correct. Then click the initiate button.
                <br>
                After clicking the initiate button, the program will run the prepare_translation() function in the
                python file you provided (or a build-in function for supported games).
                If correctly implemented, this will create four directorys in your project folder:
            <ol>
                <li> OriginalFiles: for now this folder only stores the python file defining your project (copied from
                    the path you provided)</li>
                <br>
                <li> RawText: Based on your implementaiton, this folder will contain the original script files in the
                    game that contain the text required to be translated. The files here are not parsed and will remain
                    unchanged during the entire translation process.</li>
                <br>
                <li> Text: If game files have been correctly parsed, this folder will be filled with .csv files
                    containing the text that requires translation, in a format defined as in the documentation of the
                    program.</li>
                <br>
                <li> TranslatedFiles: If you have implemented an integrate() method, this folder will contain the same
                    files as in RawText but with translated text. You can verify here if the format is correct. (For
                    certain games, you can directly patch this folder then put it in the game's folder to apply a
                    translation patch.)</li>
            </ol>
            </p>
        </div>
        <div class="option-container">
            <div class="option">
                <label for="projectName">Project Name:</label>
                <label> {{ this.project.projectName }}</label>
            </div>
            <div class="option">
                <label for="projectPath">Project Path:</label>
                <label> {{ this.project.projectPath }}</label>
            </div>
            <div class="option">
                <label for="gamePath">Game Path:</label>
                <label> {{ this.project.gamePath }}</label>
            </div>
            <div class="option">
                <label for="gameEngine">Game Engine:</label>
                <label> {{ this.project.gameEngine }}</label>
            </div>
            <div class="option">
                <label for="translator">Translator:</label>
                <label> {{ this.project.translator }}</label>
            </div>
            <div class="option">
                <label for="Language">Language:</label>
                <label>From {{ this.project.fromLanguage }} to {{ this.toLanguage }}</label>
            </div>
        </div>
        <button @click="initializeGame">Initiate Game</button>
        <div>
        </div>
    </div>
</template>

<script>
import { useStore } from 'vuex'
import axios from 'axios'
import { computed } from 'vue'
//import { ipcRenderer } from 'electron'
export default {
    name: "InitializeProject",
    props: {
    },
    data() {
        return {

        };
    },
    created() {
    },
    setup() {
        const store = useStore();
        const updateProject = (project) => {
            store.dispatch("updateProject", project);
        };
        const project = computed(() => store.state.project);
        return { updateProject, project };

    },
    methods: {
        clickNext() {
            this.displayIntro = false;
        },
        async initializeGame() {
            // add code to create the project object using python, and save to the destination path
            this.project = {
                is_initialized: true,
            }

            // await ipcRenderer.invoke("show-confirmation-dialog", 'The project is already initialized. Are your sure to re-initialize it? This action will OVERWRITE ALL TRANSLATED TEXT AND FILES. ').then(response => {
            //     if (response === 0) {
            //         return;
            //     }
            // });
            // if (!confirm) {
            //     return;
            // }
            const http = axios.create({
                baseURL: "http://localhost:5000",
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                },
            });
            http.post("/initialize_game", this.project).then((response) => {
                console.log(response.data);
            }).catch((error) => {
                console.log(error);
            })

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
