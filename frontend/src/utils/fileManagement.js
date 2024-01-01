import axios from "axios";
import store from '../store/store.js'
import { EventBus } from './eventBus.js';

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

export async function changeFileProperty(changeRequest) {
    console.log("file to be changed: ", changeRequest);
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });
    let response = await http.post("/change_file_property", changeRequest);
    console.log(response.data);
    const result = response.data;
    if (result.status === true) {
        console.log("file changed successfully!")
        return result;
    } else {
        alert("Failed to change file. Please check your the format of the file.")
        return result;
    }
}

export async function saveTextFile(file) {
    let filePath = file["filePath"]
    console.log("file to be saved: ", filePath);
    if (!(store.getters.getCurrentDisplay["type"] === "text")) {
        console.log(store.getters.getCurrentDisplay)
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
        console.log("file saved successfully!")
        return result;
    } else {
        alert("Failed to save file.")
        return result;
    }


}

export async function translateFile(filePath, temp_temperature, temp_max_lines) {
    // create the request
    let requestT = {};
    let is_translating = store.state.currentTranslation["translating"];
    if (is_translating) {
        alert("Please wait for the current translation to finish");
        return;
    }
    requestT["temperature"] = temp_temperature;
    requestT["max_lines"] = temp_max_lines;
    requestT["file_path"] = filePath;
    store.dispatch("updateTranslationFile", filePath);
    store.dispatch("updateTranslationStatus", true);
    console.log("Trying to translate : " + requestT["file_path"]);
    if (requestT["file_path"] == undefined) {
        alert("Please select a file first");
        store.dispatch("updateTranslationFile", "");
        store.dispatch("updateTranslationStatus", false);
        return;
    }
    // if file path doesn't end with .csv, then it's not a csv file
    if (!requestT["file_path"].endsWith(".csv")) {
        alert("Please select a text rather than a script file");
        store.dispatch("updateTranslationFile", "");
        store.dispatch("updateTranslationStatus", false);
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
    await http.post("http://localhost:5000/translate_text", requestT)
        .then(response => {
            // update directory tree to display tranlsation status
            EventBus.emit("updateTranslationStatus")
            store.dispatch("updateTranslationFile", "");
            store.dispatch("updateTranslationStatus", false);
            if (response.data["status"] == true) {
                if (store.state.currentDisplay["filePath"] == requestT["file_path"]) {
                    // if still displaying the same file, update manually the content
                    EventBus.emit("updateFileContent");
                }
                return;

            } else {
                alert("Failed to translate the file" + response.data["file_path"]);
                return;
            }
        });
    return;
}

export async function translateAllFiles(temp_temperature, temp_max_lines) {
    let file_list = store.state.currentFileList;
    let toTranslate = [];
    let thisCount = 1;

    let totalCount = 0;
    let translatedCount = 0;
    for (let file of file_list) {
        if (file.notTranslated) {
            totalCount += 1;
            toTranslate.push(file);
        } else {
            translatedCount += 1;
        }
    }
    console.log("total files to translate: ", totalCount);
    alert("Start to translate " + totalCount + " files. Skipping" + translatedCount + " translated files.")

    store.dispatch("updateTranslationProgress", { thisCount: thisCount, totalCount: totalCount });
    for (let file of toTranslate) {
        if (store.state.stopSignal) {
            console.log("stop signal received");
            store.dispatch("updateTranslationProgress", { thisCount: 0, totalCount: 0 });
            store.dispatch("updateTranslationStatus", false);
            store.dispatch("updateTranslationFile", "");
            store.state.stopSignal = false;
            return;
        }
        await translateFile(file["path"], temp_temperature, temp_max_lines);
        thisCount += 1;
        store.dispatch("updateTranslationProgress", { thisCount: thisCount, totalCount: totalCount });
    }

}