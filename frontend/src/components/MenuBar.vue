<template>
    <span class="menu-bar-in">
        <button @click="create_new_project">New Project</button>
        <button @click="initialize_project">Initialize </button>
        <button @click="integrate_project"> Integrate </button>
        <button @click="preferences"> Preferences </button>
        <!-- Right side dropdown -->
        <span class="menu-right">
            <!-- Endpoints dropdown -->
            <select class="menu-select" v-model="selectedEndpoint" @change="onEndpointChange">
                <option v-for="ep in endpoints" :key="ep" :value="ep">{{ ep }}</option>
            </select>

            <!-- Models dropdown (depends on endpoint) -->
            <select class="menu-select" v-model="selectedModel" @change="onModelChange" :disabled="!models.length">
                <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
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
            selectedEndpoint: null,
            selectedModel: null,
        }
    },
    computed: {
        ...mapState(['endpoints', 'models', 'currentEndpoint', 'currentModel']),
        options() {
            return this.$store.state.translators;
        },
    },
    async mounted() {
        await this.$store.dispatch('loadEndpoints')
        this.selectedEndpoint = this.currentEndpoint
        this.selectedModel = this.currentModel
    },
    watch: {
        // Keep local selects in sync if store changes elsewhere
        currentEndpoint(newVal) {
            if (newVal !== this.selectedEndpoint) this.selectedEndpoint = newVal
        },
        currentModel(newVal) {
            if (newVal !== this.selectedModel) this.selectedModel = newVal
        }
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
        async onEndpointChange() {
            if (!this.selectedEndpoint) return
            await this.$store.dispatch('selectEndpoint', this.selectedEndpoint)
            // After endpoint changes, the store will set a default model; mirror it
            this.selectedModel = this.$store.state.currentModel
        },
        async onModelChange() {
            if (!this.selectedModel) return
            await this.$store.dispatch('selectModel', this.selectedModel)
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
