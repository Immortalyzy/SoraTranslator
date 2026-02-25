const { contextBridge, ipcRenderer } = require('electron');

const DEFAULT_API_BASE = "http://127.0.0.1:5000";

function getLocationSearch() {
    try {
        if (typeof globalThis !== "undefined" &&
            globalThis.location &&
            typeof globalThis.location.search === "string") {
            return globalThis.location.search;
        }
    } catch (error) {
        // ignore missing/blocked location in preload context
    }

    return "";
}

function normalizeApiBase(value) {
    if (!value) {
        return "";
    }

    let normalized = String(value).trim();
    if (!normalized) {
        return "";
    }

    try {
        normalized = decodeURIComponent(normalized);
    } catch (error) {
        // keep original value when not URI-encoded
    }

    return normalized.replace(/\/+$/, "");
}

function resolveApiBase() {
    const cliArg = process.argv.find((arg) => arg.startsWith("--sora-api-base="));
    if (cliArg) {
        const value = normalizeApiBase(cliArg.split("=", 2)[1]);
        if (value) {
            return value;
        }
    }

    const queryValue = (() => {
        try {
            const params = new URLSearchParams(getLocationSearch());
            return normalizeApiBase(params.get("sora_api_base"));
        } catch (error) {
            return "";
        }
    })();
    if (queryValue) {
        return queryValue;
    }

    const envValue = normalizeApiBase(process.env.SORA_API_BASE);
    if (envValue) {
        return envValue;
    }

    return DEFAULT_API_BASE;
}

const runtimeConfig = Object.freeze({
    apiBase: resolveApiBase(),
});

if (typeof globalThis !== "undefined") {
    globalThis.__SORA_API_BASE__ = runtimeConfig.apiBase;
}

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

contextBridge.exposeInMainWorld("soraRuntime", {
    getApiBase: () => runtimeConfig.apiBase,
    getRuntimeConfig: () => runtimeConfig,
});

