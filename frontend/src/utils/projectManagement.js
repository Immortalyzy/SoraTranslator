import axios from "axios";
import store from '../store/store.js'


const updateProject = (project) => {
    store.dispatch("updateProject", project);
};

export async function initializeGame(project) {
    // add code to create the project object using python, and save to the destination path

    console.log("project to be initialized: ", project);
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });
    http.post("/initialize_game", project).then((response) => {
        console.log(response.data);
        const result = response.data;
        const project_new = result;
        if (result.status === true) {
            updateProject(project_new);
            alert("Game initialized successfully!")
        } else {
            updateProject(project_new);
            alert("Failed to initialize game. Please check your game definition or format.")
        }
    }).catch((error) => {
        console.log(error);
    })
}