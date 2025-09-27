import { createStore } from 'vuex'
import axios from 'axios'
const API = 'http://localhost:5000'

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
            translators: [],
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
        }

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
        async loadTranslators({ commit }) {
            const { data } = await axios.get(`${API}/translators`)
            commit('setTranslators', data.translators || [])
            if (data.current) commit('updateTranslator', data.current)
        },
        async selectTranslator({ commit }, name) {
            await axios.post(`${API}/translators/select`, { translator: name })
            commit('updateTranslator', name)
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
