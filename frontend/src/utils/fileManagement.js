import axios from "axios";
import store from '../store/store.js'


const updateProject = (project) => {
    store.dispatch("updateProject", project);
};
export async function saveFile(file, destination) {
    // add code to save the file to the destination path
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });
    let response = await http.post("/save_file", { file, destination });

    console.log(response.data);
    const result = response.data;
    const project_new = result;
    if (result.status === true) {
        updateProject(project_new);
        alert("File saved successfully!")
    } else {
        updateProject(project_new);
        alert("Failed to save file. Please check your game definition or format.")
    }
}

export async function readTextFile(filePath) {
    // add code to create the project object using python, and save to the destination path

    console.log("file to be read: ", filePath);
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });
    let response = await http.post("/require_text_json", filePath);
    console.log(response.data);
    const result = response.data;
    if (result.status === true) {
        console.log("file read successfully!")
        return result;
    } else {
        alert("Failed to read file. Please check your the format of the file.")
        return result;
    }
}

export async function translateTextFile(packed_data) {
    console.log("Sending translation request of ", packed_data['file_path']);
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });

    await http.post("/translate_text", packed_data);

}