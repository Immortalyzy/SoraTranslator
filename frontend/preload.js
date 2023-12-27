const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => ipcRenderer.send(channel, data),
        on: (channel, func) => {
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        },
        invoke: (channel, data) => ipcRenderer.invoke(channel, data),
        removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
    }
});

alert('preload.js loaded');
