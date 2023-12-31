<template>
    <div>
        <div class="new-project-title">
            <h1>WELCOME TO SORATRANSLATOR</h1>
            <h2>CREATE A PROJECT: Initailize the game </h2>
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
            <div class="option-init">
                <label for="name">Project Name:</label>
                <div class="option-show"> {{ this.project.name }}</div>
            </div>
            <div class="option-init">
                <label for="project_path">Project Path:</label>
                <div class="option-show"> {{ this.project.project_path }}</div>
            </div>
            <div class="option-init">
                <label for="game_path">Game Path:</label>
                <div class="option-show"> {{ this.project.game_path }}</div>
            </div>
            <div class="option-init">
                <label for="gameEngine">Game Engine:</label>
                <div class="option-show"> {{ this.project.gameEngine }}</div>
            </div>
            <div class="option-init">
                <label for="translator">Translator:</label>
                <div class="option-show"> {{ this.project.translator }}</div>
            </div>
            <div class="option-init">
                <label for="Language">Language:</label>
                <div class="option-show">From {{ this.project.original_language }} to {{ this.target_language }}</div>
            </div>
        </div>
        <button @click="initGame">Initiate Game</button>
        <div>
        </div>
    </div>
</template>

<script>
import { useStore } from 'vuex'
// import axios from 'axios'
import { initializeGame } from '@/utils/projectManagement'
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
        async initGame() {
            // add code to create the project object using python, and save to the destination path
            await initializeGame(this.project);

            // todo: write code here to show a project resume page

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

<style scoped>
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
    margin: 0 1%;
    flex-direction: column;
    align-items: left;
    text-align: left;
    border: white;
    overflow-x: auto;
    white-space: nowrap;
}

.option-container>* {
    height: 30px;
    font-size: 25px;
    text-align: left;
}


.option-init {
    display: inline-block;
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

.option-show {
    display: inline-block;
    color: rgb(255, 255, 255);
    width: 200px;
    flex-shrink: 0;
    flex-grow: 0;
    margin-left: 5px;
    text-align: left;
}
</style>
