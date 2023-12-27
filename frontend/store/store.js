import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({
    state: {
        // Define your application state here
        counter: 0
    },
    mutations: {
        // Define mutations to change the state
        INCREMENT(state) {
            state.counter++;
        }
    },
    actions: {
        // Define actions to commit mutations
        increment({ commit }) {
            commit('INCREMENT');
        }
    },
    getters: {
        // Define getters to retrieve state values
        counter: state => state.counter
    }
});
