<template>
    <div>
        <button :class="{ 'edited-style': isEdited }" @click="updateSettings"> Save </button>
        <button @click="fetchSettings"> Reload </button>
        <JsonEditorVue v-model="preferences" :options="{
            modes: ['tree', 'code'],
            indentation: 2,
            statusBar: true
        }" :onChange="handleEdit" />
    </div>
</template>

<script>
import axios from 'axios';
import JsonEditorVue from 'json-editor-vue';

export default {
    components: {
        JsonEditorVue,
    },
    data() {
        return {
            preferences: {},
            isEdited: false,
        };
    },
    created() {
        this.fetchSettings();
    },
    methods: {
        handleEdit() {
            this.isEdited = true;
        },
        async fetchSettings() {
            try {
                const response = await axios.get('http://localhost:5000/preferences');
                this.preferences = response.data;
            } catch (error) {
                console.error(error);
            }
        },
        async updateSettings() {
            try {
                await axios.post('http://localhost:5000/preferences', this.preferences);
                this.isEdited = false;
            } catch (error) {
                console.error(error);
            }
        },
        handleKeydown(event) {
            // Check for Ctrl+S or Command+S (for macOS)
            if ((event.ctrlKey || event.metaKey) && event.keyCode == 83) {
                event.preventDefault();  // Prevent the default save behavior
                this.updateSettings();
            }
        },
    },
    mounted() {
        document.addEventListener('keydown', this.handleKeydown);
    },
    beforeUnmount() {
        document.removeEventListener('keydown', this.handleKeydown);
    },
};
</script>

<style scoped>
button {
    width: 10%;
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

.edited-style {
    /* Add your desired styles for the edited state */
    /* animation: pulseEffect 2s ease-out infinite; */
    animation: pulseEffect 1.5s infinite;

}

@keyframes breathingEffect {

    0%,
    100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.1);
    }
}

@keyframes pulseEffect {
    0% {
        box-shadow: 0 0 0 0 rgba(250, 248, 248, 0.7);
    }

    70% {
        box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
    }

    100% {
        box-shadow: 0 0 0 0 rgba(244, 67, 54, 0);
    }
}
</style>