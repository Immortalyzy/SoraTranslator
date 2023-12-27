import { createStore } from 'vuex'

const store = createStore({
    state() {
        return {
            // your JSON variable
            project: {}
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
    }
});

export default store;
