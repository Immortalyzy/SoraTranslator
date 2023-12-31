import { createStore } from 'vuex'

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
            // stores the main display
            currentDisplay: {
                displayType: "T",
                filePath: "",
            },
            // stores the strings to be displayed in the info panel
            currentInfo: {
                text_info1: "MrVergil",
                text_info2: "Sora is best",
            },
            // stores the progress of translation and prevent new translation requests
            currentState: {

            },
        }
    },
    mutations: {
        // mutation to update your JSON variable
        updateProject(state, newJson) {
            state.project = newJson;
        },
        updateCurrentDisplay(state, newDisplay) {
            state.currentDisplay = newDisplay;
        }
    },
    actions: {
        // action to commit the mutation
        updateProject(context, newJson) {
            context.commit('updateProject', newJson);
        },
        updateCurrentDisplay(context, newDisplay) {
            context.commit('updateCurrentDisplay', newDisplay);
        }
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
