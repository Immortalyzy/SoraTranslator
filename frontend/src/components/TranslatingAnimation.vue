<template>
    <div class="translation-status">
        <div v-if="showProgress" class="text-path">{{ progressStr }} </div>
        <div class="text-path">{{ statusLabel }}</div>
        <div class="text-path">{{ displayPath }}</div>
        <div v-if="showError" class="text-path error-text">{{ errorText }}</div>
        <div class="animation-container">
            <div v-if="isTranslating" class="loader"></div>
        </div>
    </div>
</template>

<script>
import { useStore } from 'vuex';
import { computed } from 'vue';
export default {
    name: 'TranslatingAnimation',
    props: {
    },
    setup() {
        const store = useStore();

        let isTranslating = computed(() => store.state.currentTranslation.translating);
        let currentFile = computed(() => store.state.currentTranslation.filePath);
        let phase = computed(() => store.state.currentTranslation.phase || "idle");
        let errorText = computed(() => store.state.currentTranslation.error || "");
        let displayPath = computed(() => {
            if (!currentFile.value) {
                return "-";
            }
            let path = currentFile.value.split(/[/\\]/);
            return path[path.length - 1];
        });
        let progressStr = computed(() => {
            let progress = store.state.currentTranslation;
            const totalCount = Number(progress.totalCount || 0);
            const thisCount = Number(progress.thisCount || 0);
            if (totalCount <= 0) {
                return "0/0";
            }
            return Math.min(thisCount, totalCount) + "/" + totalCount;
        });
        let showProgress = computed(() => {
            if (isTranslating.value) {
                return true;
            }
            return Number(store.state.currentTranslation.totalCount || 0) > 0;
        });
        let showError = computed(() => phase.value === "failed" && !!errorText.value);
        let statusLabel = computed(() => {
            if (isTranslating.value) {
                if (phase.value === "preparing") {
                    return "Preparing";
                }
                if (phase.value === "applying_results") {
                    return "Applying results";
                }
                return "Translating";
            }
            if (phase.value === "completed") {
                return "Completed";
            }
            if (phase.value === "failed") {
                return "Failed";
            }
            return "Idle";
        });
        return { isTranslating, displayPath, progressStr, showProgress, showError, statusLabel, errorText };
    }
};
</script>

<style scoped>
.translation-status {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    width: 20vw;
}

.text-path {
    color: #fff;
    font-size: 25px;
    font-weight: bold;
    padding: 0 0;
    margin: 0px 0px;
    text-align: right;

}

.error-text {
    max-width: 25vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.animation-container {
    display: flex;
    justify-content: center;
    /* Center the child horizontally */
    align-items: center;
    height: 50px;
    width: 50px;
    /* Complete border style */
    border-radius: 5px;
    position: relative;
    /* Added for absolute positioning of child */
}

/* Following load code belongs to Author: Iván Villamil
from https://www.sliderrevolution.com/resources/css-loaders/ */
.loader {
    animation: rotate 1s infinite;
    height: 50px;
    width: 50px;
}

.loader:before,
.loader:after {
    border-radius: 50%;
    content: '';
    display: block;
    height: 20px;
    width: 20px;
}

.loader:before {
    animation: ball1 1s infinite;
    background-color: #cb2025;
    box-shadow: 30px 0 0 #f8b334;
    margin-bottom: 10px;
}

.loader:after {
    animation: ball2 1s infinite;
    background-color: #00a096;
    box-shadow: 30px 0 0 #97bf0d;
}

@keyframes rotate {
    0% {
        -webkit-transform: rotate(0deg) scale(0.8);
        -moz-transform: rotate(0deg) scale(0.8);
    }

    50% {
        -webkit-transform: rotate(360deg) scale(1.2);
        -moz-transform: rotate(360deg) scale(1.2);
    }

    100% {
        -webkit-transform: rotate(720deg) scale(0.8);
        -moz-transform: rotate(720deg) scale(0.8);
    }
}

@keyframes ball1 {
    0% {
        box-shadow: 30px 0 0 #f8b334;
    }

    50% {
        box-shadow: 0 0 0 #f8b334;
        margin-bottom: 0;
        -webkit-transform: translate(15px, 15px);
        -moz-transform: translate(15px, 15px);
    }

    100% {
        box-shadow: 30px 0 0 #f8b334;
        margin-bottom: 10px;
    }
}

@keyframes ball2 {
    0% {
        box-shadow: 30px 0 0 #97bf0d;
    }

    50% {
        box-shadow: 0 0 0 #97bf0d;
        margin-top: -20px;
        -webkit-transform: translate(15px, 15px);
        -moz-transform: translate(15px, 15px);
    }

    100% {
        box-shadow: 30px 0 0 #97bf0d;
        margin-top: 0;
    }
}
</style>
