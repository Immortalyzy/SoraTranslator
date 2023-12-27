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
                    <label for="projectPath">Project Path:</label>
                    <input type="text" id="gameEngine" name="gameEngine" v-model="gameEngine">
                    <button @click="selectProjectPath">...</button>
                </div>
                <div class="option">
                    <label for="gamePath">Game Path:</label>
                    <input type="file" id="gamePath" name="gamePath" v-on:change="changeGamePath">
                </div>
                <div class="option">
                    <label for="gameEngine">Game Engine:</label>
                    <input type="text" id="gameEngine" name="gameEngine" v-model="gameEngine">
                </div>
                <div class="option">
                    <label for="translator">Translator:</label>
                    <input type="text" id="translator" name="translator" v-model="translator">
                </div>
                <div class="option">
                    <label for="Language">Language:</label>
                    <input class="half-input" type="text" id="fromLanguage" name="fromLanguage" v-model="fromLanguage">
                    >
                    <input class="half-input" type="text" id="toLanguage" name="toLanguage" v-model="toLanguage">
                </div>
            </div>
            <div>
                DEBUG:
                {{ projectPath }}
                {{ gamePath }}
                {{ translator }}
                {{ fromLanguage }}
                {{ toLanguage }}
            </div>
            <button @click="createProject">Create</button>
            <div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: "NewProject",
    props: {
    },
    data() {
        return {
            // for new project
            projectPath: "",
            gamePath: "",
            translator: "",
            fromLanguage: "",
            toLanguage: "",

            // for page display
            displayIntro: true,

        };
    },
    methods: {
        clickNext() {
            this.displayIntro = false;
        },
        createProject() {
            alert("Project created!");
        },
        async selectProjectPath() {
            const { filePaths } = await this.$electron.remote.dialog.showOpenDialog({
                properties: ['openDirectory']
            });
            if (filePaths.length > 0) {
                this.projectPath = filePaths[0];
            }
        },
        changeProjectPath(path) {
            this.projectPath = path.target;
        },
        changeGamePath(path) {
            const file = path.target.files[0];
            if (file) {
                this.gamePath = file.name;
            }
        },
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
    margin: 0 20%;
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

label {
    display: inline-block;
    color: rgb(255, 255, 255);
    width: 200px;
    flex-shrink: 0;
    flex-grow: 0;
    text-align: right;
}

.option {
    color: white;
    flex-basis: 5%;
}

input {
    font-size: 25px;
    color: rgb(255, 255, 255);
    background-color: rgba(0, 0, 0, 0.295);
    border: 1px solid #ffd0d0;
    border-radius: 5px;
    width: 500px;
    flex-shrink: 0;
    flex-grow: 0;
    text-align: left;
}

.half-input {
    width: 200px;
    flex-shrink: 0;
    flex-grow: 0;
    text-align: left;
}
</style>
