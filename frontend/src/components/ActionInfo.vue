<template>
    <div class="action-info-block">
        <div class="actions">
            <button @click="translate">Translate all files</button>
            <button> Translate this file</button>
            <div class="action-value">

                <input type="text" placeholder="Enter the file name" />
            </div>
            <button @click="save_project">Save Project</button>
        </div>
        <div class="information">
            Information
        </div>
    </div>
</template>

<script>
export default {
    name: 'ActionInfo',
    methods: {
        translate() {
            // open a window of selecting local files
            alert("Not implemented yet");
        },
        save_project() {
        }
    }
};
</script>

<style scoped>
.action-info-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0 0;
    padding: 0 0;
}

.action-info-block>* {
    margin: 0 0;
    padding: 0 0;
    width: 100%;
}

.actions {
    margin: 0px 0px;
    height: 50%;
    border: #ffd0d0;
}

.information {
    margin: 0px 0px;
    padding: 0px 00px;
    font-size: large;
    align-items: center;
    display: inline-block;
    border: 1px solid #ffd0d0;
    color: rgb(255, 255, 255);
    text-align: left;
    text-decoration: none;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
    /* Red glow */
    height: 50%;
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

button :hover {
    background-color: rgb(255, 255, 255);
    color: rgb(179, 116, 0);
    border-color: rgb(179, 116, 0);
}
</style>
