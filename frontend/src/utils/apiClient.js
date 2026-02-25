/* global globalThis */
import axios from "axios";

const DEFAULT_API_BASE = "http://127.0.0.1:5000";

let cachedApiBase = null;

function getLocationSearch() {
    try {
        if (typeof globalThis !== "undefined" &&
            globalThis.location &&
            typeof globalThis.location.search === "string") {
            return globalThis.location.search;
        }
    } catch (error) {
        // ignore location access issues
    }

    return "";
}

function getRuntimeBridgeApiBase() {
    if (typeof globalThis === "undefined") {
        return "";
    }

    const runtime = globalThis.soraRuntime;
    if (!runtime || typeof runtime.getApiBase !== "function") {
        return "";
    }

    return runtime.getApiBase();
}

function getGlobalInjectedApiBase() {
    if (typeof globalThis === "undefined") {
        return "";
    }

    return globalThis.__SORA_API_BASE__;
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

export function getApiBase() {
    if (cachedApiBase) {
        return cachedApiBase;
    }

    const runtimeValue = normalizeApiBase(getRuntimeBridgeApiBase());
    const globalInjectedValue = normalizeApiBase(getGlobalInjectedApiBase());
    const queryValue = (() => {
        try {
            return normalizeApiBase(new URLSearchParams(getLocationSearch()).get("sora_api_base"));
        } catch (error) {
            return "";
        }
    })();

    const base = runtimeValue || globalInjectedValue || queryValue || DEFAULT_API_BASE;
    cachedApiBase = normalizeApiBase(base) || DEFAULT_API_BASE;
    return cachedApiBase;
}

export function createApiClient(method = "POST") {
    return axios.create({
        baseURL: getApiBase(),
        method,
        headers: {
            "Content-type": "application/json",
        },
    });
}

export function apiGet(path, config) {
    return axios.get(`${getApiBase()}${path}`, config);
}

export function apiPost(path, data, config) {
    return axios.post(`${getApiBase()}${path}`, data, config);
}
