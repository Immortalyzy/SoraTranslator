const { ipcRenderer } = require('electron');

const listFiles = async (path) => {
    return ipcRenderer.invoke('list-files', path);
};

export { listFiles };
