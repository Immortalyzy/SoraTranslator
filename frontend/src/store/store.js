import { createStore } from 'vuex'

const store = createStore({
    state() {
        return {
            // your JSON variable
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
            currentDisplay: {
                displayType: "T",
                filePath: "",
            },
            currentInfo: {

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
            console.log("project updated to ", newJson);
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
