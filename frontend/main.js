const { app, BrowserWindow } = require('electron');
const path = require('path');

const { ipcMain, dialog } = require('electron');

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



function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true
        },
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true
        }

    });
    // load public index.html for development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:8080');
    }
    else {
        mainWindow.loadURL(`file://${__dirname}/dist/index.html`);
    }
    // Open the DevTools. You can comment this line if you don't need debugging tools.
    mainWindow.webContents.openDevTools();

    // Emitted when the window is closed.
    mainWindow.on('closed', function () {
        // Dereference the window object, usually you would store windows
        // in an array if your app supports multi windows, this is the time
        // when you should delete the corresponding element.
        mainWindow = null;
    });
}

app.on('ready', createWindow);


// Quit when all windows are closed.
app.on('window-all-closed', function () {
    // On macOS it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createWindow();
    }
});