import { createStore } from 'vuex'
import axios from 'axios'
import { getApiBase } from '../utils/apiClient'
const API = getApiBase()

const store = createStore({
    state() {
        return {
            // project stores the project information,
            project: {
                name: '',
                prject_file_path: '',
                game_path: '', // path to the game definition file
                project_path: '', // root path of the project, containing following folders
                original_files_directory: '',
                rawtext_directory: '',
                text_directory: '',
                translated_files_directory: '',
            },
            currentFileList: [],
            // stores the translator, based on this change the display of the top-right corner
            currentTranslator: "galtransl",
            // stores the main display
            currentDisplay: {
                type: "text",
                filePath: "",
            },
            // stores the strings to be displayed in the info panel
            currentInfo: {
                text_info1: "Kasugano Sora",
                text_info2: "Sora is best",
            },
            // stores the progress of translation and prevent new translation requests
            currentState: {

            },
            currentTranslation: {
                translating: false,
                filePath: "",
                thisCount: 1,
                totalCount: 1,
            },
            stopSignal: false,
            endpoints: [],
            models: [],
        }
    },
    mutations: {
        // mutation to update your JSON variable
        updateProject(state, newJson) {
            state.project = newJson;
        },
        setTranslators(state, names) {
            state.translators = names || []
        },
        updateTranslator(state, name) {
            state.currentTranslator = name
        },
        updateFileList(state, newFileList) {
            state.currentFileList = newFileList;
        },
        updateCurrentDisplay(state, newDisplay) {
            state.currentDisplay = newDisplay;
        },
        updateCurrentInfo(state, newInfo) {
            state.currentInfo = newInfo;
        },
        updateTranslationFile(state, newFilePath) {
            state.currentTranslation.filePath = newFilePath;
        },
        updateTranslationStatus(state, newStatus) {
            state.currentTranslation.translating = newStatus;
        },
        updateTranslationProgress(state, newProgress) {
            state.currentTranslation.thisCount = newProgress["thisCount"];
            state.currentTranslation.totalCount = newProgress["totalCount"];
        },
        setEndpoints(state, names) { state.endpoints = names || [] },
        setModels(state, names) { state.models = names || [] },
        updateEndpoint(state, name) { state.currentEndpoint = name },
        updateModel(state, name) { state.currentModel = name },

    },
    actions: {
        // action to commit the mutation
        updateProject(context, newJson) {
            context.commit('updateProject', newJson);
        },
        updateTranslator(context, newTranslator) {
            context.commit('updateTranslator', newTranslator);
        },
        updateFileList(context, newFileList) {
            context.commit('updateFileList', newFileList);
        },
        updateCurrentDisplay(context, newDisplay) {
            context.commit('updateCurrentDisplay', newDisplay);
        },
        updateCurrentInfo(context, newInfo) {
            context.commit('updateCurrentInfo', newInfo);
        },
        updateTranslationFile(context, newFilePath) {
            context.commit('updateTranslationFile', newFilePath);
        },
        updateTranslationStatus(context, newStatus) {
            context.commit('updateTranslationStatus', newStatus);
        },
        updateTranslationProgress(context, newProgress) {
            context.commit('updateTranslationProgress', newProgress);
        },
        async loadEndpoints({ commit, dispatch }) {
            const { data } = await axios.get(`${API}/endpoints`)
            commit('setEndpoints', data.endpoints || [])
            if (data.current) {
                commit('updateEndpoint', data.current)
                // also load models for the current endpoint
                await dispatch('loadModels', data.current)
            }
        },
        async loadModels({ commit }, endpointName) {
            const { data } = await axios.get(`${API}/endpoints/${encodeURIComponent(endpointName)}/models`)
            commit('setModels', data.models || [])
            if (data.current) commit('updateModel', data.current)
            else if (data.models?.length) commit('updateModel', data.models[0])
            else commit('updateModel', null)
        },
        async selectEndpoint({ commit, dispatch }, endpointName) {
            await axios.post(`${API}/endpoints/select`, { endpoint: endpointName })
            commit('updateEndpoint', endpointName)
            // refresh models for this endpoint (and set default currentModel)
            await dispatch('loadModels', endpointName)
        },
        async selectModel({ commit }, modelName) {
            await axios.post(`${API}/models/select`, { model: modelName })
            commit('updateModel', modelName)
        },
    },
    getters: {
        // getter to access your JSON variable
        getProject(state) {
            return state.project;
        },
        getCurrentDisplay(state) {
            return state.currentDisplay;
        },
    }
});

export default store;
