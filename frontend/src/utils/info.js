// this files stores the method of displaying an info
import axios from "axios";
import store from '../store/store.js'

export async function requestFileInfo() {
    const filePath = store.state.currentDisplay.filePath;
    const fileType = store.state.currentDisplay.type;
    console.log(store.state.currentDisplay)
    let fileInfoRequest = {}
    fileInfoRequest["file_path"] = filePath;
    fileInfoRequest["file_type"] = fileType;
    console.log(fileInfoRequest)
    const http = axios.create({
        baseURL: "http://localhost:5000",
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
    });

    // send the request
    await http.post("http://localhost:5000/request_file_info", fileInfoRequest)
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