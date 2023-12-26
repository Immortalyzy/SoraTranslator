<template>
    <span class="menu-bar-in">
        <button @click="create_new_project">New Project</button>
        <button @click="save_project">Save Project</button>
    </span>
</template>

<script>
export default {
    name: 'MenuBar',
    methods: {
        create_new_project() {
            // open a window of selecting local files
        },
        save_project() {
        }
    }
};
</script>

<style scoped>
.menu-bar-in {
    text-align: left;
    align-items: center;
    display: flex;
    width: 100vw;
    height: 7vh;
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
</style>
