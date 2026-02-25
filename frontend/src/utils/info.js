// this files stores the method of displaying an info
import store from '../store/store.js'
import { createApiClient } from './apiClient';

export async function requestFileInfo() {
    const filePath = store.state.currentDisplay.filePath;
    const fileType = store.state.currentDisplay.type;
    console.log(store.state.currentDisplay)
    let fileInfoRequest = {}
    fileInfoRequest["file_path"] = filePath;
    fileInfoRequest["file_type"] = fileType;
    console.log(fileInfoRequest)
    const http = createApiClient("POST");

    // send the request
    await http.post("/request_file_info", fileInfoRequest)
        .then(response => {
            // update directory tree to display tranlsation status
            if (response.data["status"] == true) {
                store.dispatch("updateCurrentInfo", response.data["info"]);
                return;
            } else {
                alert("Failed to retrive the file info");
                return;
            }
        });
}
