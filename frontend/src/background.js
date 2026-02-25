'use strict'

import { app, protocol, BrowserWindow } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer'
const isDevelopment = process.env.NODE_ENV !== 'production'
const path = require('path');
const fs = require('fs');
const { URL } = require('url');

const { ipcMain, dialog } = require('electron');

function resolveApiBase() {
  const configured = process.env.SORA_API_BASE;
  if (configured && configured.trim()) {
    return configured.replace(/\/+$/, '');
  }

  const fallbackPort = process.env.SORA_BACKEND_PORT || '5000';
  return `http://127.0.0.1:${fallbackPort}`;
}

// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app', privileges: {
      secure: true,
      standard: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true
    }
  }
])

async function createWindow() {
  const apiBase = resolveApiBase();
  process.env.SORA_API_BASE = apiBase;
  const encodedApiBase = encodeURIComponent(apiBase);

  // Create the browser window.
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      additionalArguments: [`--sora-api-base=${encodedApiBase}`],
      //preload: 'app://./preload.js',
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    const devUrl = new URL(process.env.WEBPACK_DEV_SERVER_URL);
    devUrl.searchParams.set('sora_api_base', encodedApiBase);
    await win.loadURL(devUrl.toString())
    if (!process.env.IS_TEST) win.webContents.openDevTools()
  } else {
    // Load the index.html when not in development
    const indexUrl = new URL(`file://${path.join(__dirname, 'index.html')}`);
    indexUrl.searchParams.set('sora_api_base', encodedApiBase);
    await win.loadURL(indexUrl.toString());
  }
}

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    // Install Vue Devtools
    try {
      await installExtension(VUEJS3_DEVTOOLS)
    } catch (e) {
      console.error('Vue Devtools failed to install:', e.toString())
    }
  }
  createWindow()
})

// Exit cleanly on request from parent process in development mode.
if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}


ipcMain.on('open-directory-dialog', (event) => {
  dialog.showOpenDialog({
    properties: ['openDirectory']
  }).then(result => {
    if (!result.canceled && result.filePaths.length > 0) {
      console.log(result.filePaths[0]);
      event.sender.send('selected-path', result.filePaths[0]);
    }
  }).catch(err => {
    console.log(err);
  });
});

ipcMain.on('open-file-dialog', (event) => {
  dialog.showOpenDialog({
    properties: ['openFile']
  }).then(result => {
    if (!result.canceled && result.filePaths.length > 0) {
      console.log(result.filePaths[0]);
      event.sender.send('selected-path', result.filePaths[0]);
    }
  }).catch(err => {
    console.log(err);
  });
});

ipcMain.handle('select-file-dialog', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile']
  })
  if (!result.canceled && result.filePaths.length > 0) {
    console.log(result.filePaths[0]);
    return result.filePaths[0];
  }
});

ipcMain.handle('show-confirmation-dialog', async (message) => {
  const options = {
    type: 'warning',
    buttons: ['YES', 'No'],
    defaultId: 1,
    title: 'Confirmation',
    message: message,
  };
  let response = dialog.showMessageBoxSync(options);
  return response.response === 0;
});

const listFilesRecursively = (dir, fileList = [], parentDir = '') => {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      listFilesRecursively(filePath, fileList, path.join(parentDir, file));
    } else {
      fileList.push({
        path: filePath,
        displayPath: parentDir ? file + " -- " + parentDir : file
      });
    }
  });
  return fileList;
};

ipcMain.handle('list-files', async (event, directoryPath) => {
  return listFilesRecursively(directoryPath);
});


// write function to read file raw content
// text files (table format) should use Python API
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf16le');
    return content;
  } catch (err) {
    console.log(err);
    const content = "Please select a file";
    return content;
  }
});
