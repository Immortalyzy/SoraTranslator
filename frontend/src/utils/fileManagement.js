import store from '../store/store.js'
import { EventBus } from './eventBus.js';
import { createApiClient } from './apiClient';

const GALTRANSL_PROGRESS_POLL_MS = 1000;
export const GLOBAL_NAME_REPLACEMENT_FILENAME = "__global_name_replacement__.csv";

export function isGlobalNameReplacementFilePath(filePath) {
    if (!filePath || typeof filePath !== "string") {
        return false;
    }
    return filePath.toLowerCase().endsWith(GLOBAL_NAME_REPLACEMENT_FILENAME.toLowerCase());
}

function toSafeCount(value, fallback = 0) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 0) {
        return fallback;
    }
    return Math.floor(parsed);
}

function applyGalTranslProgress(progress) {
    if (!progress || typeof progress !== "object") {
        return;
    }
    const current = store.state.currentTranslation;
    const totalCount = toSafeCount(progress.totalCount, current.totalCount || 0);
    const completedCount = toSafeCount(progress.completedCount, current.thisCount || 0);
    const thisCount = totalCount > 0 ? Math.min(completedCount, totalCount) : completedCount;
    const phase = progress.phase || current.phase || "idle";
    const filePath = progress.currentFile || current.filePath || "";
    const error = progress.error || "";
    store.dispatch("updateTranslationProgress", {
        thisCount,
        totalCount,
        filePath,
        phase,
        error,
    });
}

async function requestGalTranslProgress(http) {
    const response = await http.post("/translate_project_progress", {});
    if (response.data && response.data.status === true) {
        applyGalTranslProgress(response.data.progress || {});
    }
}

export async function readTextFile(filePath) {
    console.log("file to be read: ", filePath);
    const http = createApiClient("POST");
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
    const http = createApiClient("POST");
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
    const http = createApiClient("POST");
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
    store.dispatch("updateTranslationPhase", "running");
    store.dispatch("updateTranslationError", "");
    console.log("Trying to translate : " + requestT["file_path"]);
    if (requestT["file_path"] == undefined) {
        alert("Please select a file first");
        store.dispatch("updateTranslationFile", "");
        store.dispatch("updateTranslationStatus", false);
        store.dispatch("updateTranslationPhase", "idle");
        return;
    }
    // if file path doesn't end with .csv, then it's not a csv file
    if (!requestT["file_path"].endsWith(".csv")) {
        alert("Please select a text rather than a script file");
        store.dispatch("updateTranslationFile", "");
        store.dispatch("updateTranslationStatus", false);
        store.dispatch("updateTranslationPhase", "idle");
        return;
    }
    if (isGlobalNameReplacementFilePath(requestT["file_path"])) {
        alert("Global name replacement table is settings-only and cannot be translated.");
        store.dispatch("updateTranslationFile", "");
        store.dispatch("updateTranslationStatus", false);
        store.dispatch("updateTranslationPhase", "idle");
        return;
    }
    const http = createApiClient("POST");

    // send the request
    await http.post("/translate_text", requestT)
        .then(response => {
            // update directory tree to display tranlsation status
            EventBus.emit("updateTranslationStatus")
            store.dispatch("updateTranslationFile", "");
            store.dispatch("updateTranslationStatus", false);
            store.dispatch("updateTranslationPhase", "idle");
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
    if (store.state.currentTranslator === "gpt") {
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
    if (store.state.currentTranslator === "galtransl") {
        // call translateProject instead
        console.log("Calling translateProject");
        alert("Start to translate the whole project using GalTransl.")
        let requestT = {};
        let is_translating = store.state.currentTranslation["translating"];
        if (is_translating) {
            alert("Please wait for the current translation to finish");
            return;
        }
        requestT["project_file_path"] = store.state.project["project_file_path"];

        const http = createApiClient("POST");
        let stopPolling = false;
        let pollingTimer = null;
        const pollProgress = async () => {
            if (stopPolling) {
                return;
            }
            try {
                await requestGalTranslProgress(http);
            } catch (error) {
                // Keep previous progress and continue polling on temporary failures.
                console.warn("GalTransl progress poll failed:", error);
            }
        };
        const startPolling = async () => {
            await pollProgress();
            pollingTimer = setInterval(() => {
                pollProgress();
            }, GALTRANSL_PROGRESS_POLL_MS);
        };
        const endPolling = async () => {
            stopPolling = true;
            if (pollingTimer !== null) {
                clearInterval(pollingTimer);
            }
            try {
                await requestGalTranslProgress(http);
            } catch (error) {
                console.warn("Final GalTransl progress fetch failed:", error);
            }
        };

        store.dispatch("updateTranslationStatus", true);
        store.dispatch("updateTranslationPhase", "preparing");
        store.dispatch("updateTranslationError", "");
        store.dispatch("updateTranslationProgress", {
            thisCount: 0,
            totalCount: 0,
            filePath: "",
            phase: "preparing",
            error: "",
        });

        // send the request
        alert("sending request to translate project");
        try {
            await startPolling();
            const response = await http.post("/translate_project", requestT);
            await endPolling();
            // update directory tree to display tranlsation status
            EventBus.emit("updateTranslationStatus")
            if (response.data["status"] == true) {
                store.dispatch("updateTranslationPhase", "completed");
                EventBus.emit("updateFileContent");
            } else {
                store.dispatch("updateTranslationPhase", "failed");
                store.dispatch("updateTranslationError", response.data["error"] || "GalTransl translation failed.");
                alert("Translation process failed, please check backend logs.");
            }
        } catch (error) {
            await endPolling();
            if (error.response && error.response.status === 409) {
                alert(error.response.data?.error || "GalTransl translation is already running.");
            } else {
                const errorMessage = error.response?.data?.error || error.message || "Unknown GalTransl error.";
                store.dispatch("updateTranslationPhase", "failed");
                store.dispatch("updateTranslationError", errorMessage);
                alert("Translation process failed: " + errorMessage);
            }
        } finally {
            store.dispatch("updateTranslationStatus", false);
            if (!["completed", "failed"].includes(store.state.currentTranslation.phase)) {
                store.dispatch("updateTranslationPhase", "idle");
            }
        }

    }

}
