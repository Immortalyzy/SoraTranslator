<template>
    <span class="menu-bar-in">
        <button @click="create_new_project">New Project</button>
        <button @click="initialize_project">Initialize </button>
        <button @click="integrate_project"> Integrate </button>
        <button @click="preferences"> Preferences </button>
        <!-- Right side dropdown -->
        <span class="menu-right">
            <select class="menu-select" v-model="selectedValue" @change="onSelectChange">
                <option v-for="opt in translators" :key="opt" :value="opt">
                    {{ opt }}
                </option>
            </select>
        </span>
    </span>
</template>

<script>
import { initializeGame } from '@/utils/projectManagement'
import { mapState } from 'vuex'
import axios from 'axios'
export default {
    name: 'MenuBar',
    data() {
        return {
            selectedValue: null, // holds the currently selected dropdown value
        }
    },
    computed: {
        ...mapState(['translators', 'currentTranslator']),
        options() {
            return this.$store.state.translators;
        },
    },
    async mounted() {
        // Load list + current selection from backend
        await this.$store.dispatch('loadTranslators')
        // sync local v-model
        this.selectedValue = this.currentTranslator || (this.translators[0] || null)
    },
    methods: {
        create_new_project() {
            // open a window of selecting local files
            this.$emit('change-display-type', 'new_project', "none");
        },
        save_project() {
        },
        async initialize_project() {
            const project = this.$store.state.project;
            await initializeGame(project);
        },
        async integrate_project() {
            let integrateRequest = {};
            integrateRequest.project_file_path = this.$store.state.project.project_file_path;
            alert("Integrating project: " + integrateRequest.project_file_path)
            const http = axios.create({
                baseURL: "http://localhost:5000",
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                },
            });
            await http.post("/integrate_game", integrateRequest).then((response) => {
                console.log(response.data);
                const reponseInfo = response.data;
                alert("Integration finished. " + reponseInfo["indication"]);
            }).catch((error) => {
                console.log(error);
            })
        },
        preferences() {
            // change the display type to preferences
            this.$emit('change-display-type', 'preferences', "none");
        },
        // Handle dropdown change of translators
        async onSelectChange() {
            if (!this.selectedValue) return
            // update both backend and store
            await this.$store.dispatch('selectTranslator', this.selectedValue)
            // (Optional) show a toast/alert
            // alert(`Selected translator: ${this.selectedValue}`)
        },

    }
};
</script>

<style scoped>
.menu-bar-in {
    text-align: left;
    align-items: center;
    display: flex;
    width: 100vw;
    padding: 0px 0;
    margin: 0px 0;
    border: rgb(75, 0, 0);
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

.menu-select {
    margin: 0 8px;
    padding: 6px 10px;
    font-size: 14px;
    border: 1px solid #ffd0d0;
    background: #fff;
    color: #333;
    border-radius: 4px;
}
</style>
