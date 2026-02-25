<template>
    <div>
        <div class="simple-setup">
            <div class="section-title">Quick Key Setup</div>
            <div class="row">
                <label>Endpoint</label>
                <select v-model="setup.endpoint" @change="onEndpointChange">
                    <option v-for="ep in setup.endpoints" :key="ep.name" :value="ep.name">{{ ep.name }}</option>
                </select>
            </div>
            <div class="row">
                <label>Model</label>
                <select v-model="setup.model">
                    <option v-for="m in setup.models" :key="m" :value="m">{{ m }}</option>
                </select>
            </div>
            <div class="row">
                <label>API Key</label>
                <input type="password" v-model="setup.apiKey" placeholder="Enter API key" />
            </div>
            <div class="row">
                <label>Proxy</label>
                <input type="text" v-model="setup.proxy" placeholder="Optional, e.g. http://127.0.0.1:10809" />
            </div>
            <div class="row row-actions">
                <button @click="saveEssentialSetup">Save Key Setup</button>
            </div>
        </div>

        <div class="editor-actions">
            <button :class="{ 'edited-style': isEdited }" @click="updateSettings"> Save </button>
            <button @click="fetchSettings"> Reload </button>
        </div>

        <JsonEditorVue ref="editor" v-model="preferences" :options="{
            modes: ['tree', 'code'],
            indentation: 2,
            statusBar: true
        }" :onChange="handleEdit" />
    </div>
</template>

<script>
import axios from 'axios';
import JsonEditorVue from 'json-editor-vue';
import { getApiBase } from '@/utils/apiClient';

const API_BASE = getApiBase();

export default {
    components: {
        JsonEditorVue,
    },
    data() {
        return {
            preferences: {},
            isEdited: false,
            setup: {
                endpoints: [],
                endpoint: '',
                models: [],
                model: '',
                apiKey: '',
                proxy: '',
            },
        };
    },
    created() {
        this.fetchSettings();
        this.fetchSetupOptions();
    },
    methods: {
        handleEdit(updatedContent) {
            if (updatedContent?.json !== undefined) {
                this.preferences = updatedContent.json;
            } else if (updatedContent?.text !== undefined) {
                try {
                    this.preferences = JSON.parse(updatedContent.text);
                } catch (_) {
                    this.preferences = updatedContent.text;
                }
            }
            this.isEdited = true;
        },
        async fetchSettings() {
            try {
                const response = await axios.get(`${API_BASE}/preferences`);
                this.preferences = response.data;
                this.isEdited = false;
            } catch (error) {
                console.error(error);
            }
        },
        async fetchSetupOptions() {
            try {
                const { data } = await axios.get(`${API_BASE}/setup/options`);
                this.setup.endpoints = data.endpoints || [];
                const endpointFromServer = data.current?.endpoint;
                this.setup.endpoint = endpointFromServer || (this.setup.endpoints[0]?.name || '');
                this.syncModelsFromEndpoint();
                const serverModel = data.current?.model;
                this.setup.model = serverModel && this.setup.models.includes(serverModel)
                    ? serverModel
                    : (this.setup.models[0] || '');
                this.setup.proxy = data.current?.proxy || '';
                this.setup.apiKey = '';
            } catch (error) {
                console.error(error);
            }
        },
        syncModelsFromEndpoint() {
            const endpointObj = this.setup.endpoints.find(ep => ep.name === this.setup.endpoint);
            this.setup.models = endpointObj?.models || [];
            if (!this.setup.models.includes(this.setup.model)) {
                this.setup.model = this.setup.models[0] || '';
            }
        },
        onEndpointChange() {
            this.syncModelsFromEndpoint();
        },
        async saveEssentialSetup() {
            if (!this.setup.endpoint) {
                alert('Please select an endpoint.');
                return;
            }
            if (!this.setup.model) {
                alert('Please select a model.');
                return;
            }
            if (!this.setup.apiKey || !this.setup.apiKey.trim()) {
                alert('API key is required.');
                return;
            }

            try {
                await axios.post(`${API_BASE}/setup/save`, {
                    endpoint: this.setup.endpoint,
                    model: this.setup.model,
                    api_key: this.setup.apiKey.trim(),
                    proxy: this.setup.proxy?.trim() || '',
                });
                this.setup.apiKey = '';
                await this.fetchSettings();
                alert('Key setup saved.');
            } catch (error) {
                const message = error?.response?.data?.error || 'Failed to save key setup.';
                alert(message);
            }
        },
        async updateSettings() {
            try {
                const latest = this.$refs.editor?.jsonEditor?.get?.();

                let payload = latest?.json;
                if (payload === undefined) {
                    const textValue = latest?.text ?? this.preferences;
                    if (typeof textValue === 'string') {
                        payload = JSON.parse(textValue);
                    } else {
                        payload = textValue;
                    }
                }

                await axios.post(
                    `${API_BASE}/preferences`,
                    payload,
                    { headers: { 'Content-Type': 'application/json' } }
                );

                this.isEdited = false;
            } catch (error) {
                console.error(error);
                alert('Failed to save preferences. Please make sure the JSON is valid.');
            }
        },
        handleKeydown(event) {
            if ((event.ctrlKey || event.metaKey) && event.keyCode == 83) {
                event.preventDefault();
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
.simple-setup {
    border: 1px solid #ffd0d0;
    padding: 8px;
    margin: 8px 0;
    background: rgba(30, 0, 0, 0.35);
}

.section-title {
    color: #fff;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
}

.row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    gap: 8px;
}

.row label {
    width: 90px;
    color: #fff;
    font-weight: 600;
}

.row select,
.row input {
    flex: 1;
    background-color: rgba(0, 0, 0, 0.35);
    color: #fff;
    border: 1px solid #ffd0d0;
    padding: 4px 6px;
}

.row-actions {
    justify-content: flex-end;
}

.editor-actions {
    display: flex;
    gap: 8px;
}

button {
    margin: 5px 5px;
    padding: 5px 10px;
    font-size: large;
    border: 1px solid #ffd0d0;
    background-color: rgb(179, 116, 0);
    color: rgb(255, 255, 255);
    text-align: center;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
}

.edited-style {
    animation: pulseEffect 1.5s infinite;
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
