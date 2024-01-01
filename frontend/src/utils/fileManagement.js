import axios from "axios";
import store from '../store/store.js'
import { EventBus } from './eventBus.js';


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

export async function saveTextFile(file) {
    let filePath = file["filePath"]
    console.log("file to be saved: ", filePath);
    if (!(store.getters.getCurrentDisplay["displayType"] === "T")) {
        alert("Editing non-text file is not supported yet.");
        return;
    }
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });
    let response = await http.post("/save_text_from_json", file);
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
export async function translateFile(filePath, temp_temperature, temp_max_lines) {
    // create the request
    let requestT = {};
    requestT["temperature"] = temp_temperature;
    requestT["max_lines"] = temp_max_lines;
    requestT["file_path"] = filePath;
    console.log("Trying to translate : " + requestT["file_path"]);
    if (requestT["file_path"] == undefined) {
        alert("Please select a file first");
        return;
    }
    // if file path doesn't end with .csv, then it's not a csv file
    if (!requestT["file_path"].endsWith(".csv")) {
        alert("Please select a text rather than a script file");
        return;
    }
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });

    // send the request
    http.post("http://localhost:5000/translate_text", requestT)
        .then(response => {
            // update directory tree to display tranlsation status
            EventBus.emit("updateTranslationStatus")
            if (response.data["status"] == true) {
                if (store.state.currentDisplay["filePath"] == requestT["file_path"]) {
                    // if still displaying the same file, update manually the content
                    EventBus.emit("updateFileContent");
                }

            } else {
                alert("Failed to translate the file" + response.data["file_path"]);
            }
        });

}