import { createStore } from 'vuex'

const store = createStore({
    state() {
        return {
            // your JSON variable
            project: {
                name: '',
                description: '',
                rawtext_directory: '',
                text_directory: '',
                translated_files_directory: '',
            },
            currentDisplay: {
                displayType: "T",
                filePath: "",
            }
        }
    },
    mutations: {
        // mutation to update your JSON variable
        updateProject(state, newJson) {
            state.project = newJson;
        }
    },
    actions: {
        // action to commit the mutation
        updateProject(context, newJson) {
            context.commit('updateProject', newJson);
        }
    },
    getters: {
        // getter to access your JSON variable
        getProject(state) {
            return state.project;
        }
    }
});

export default store;
