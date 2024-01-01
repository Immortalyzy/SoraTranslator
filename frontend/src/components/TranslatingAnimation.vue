<template>
    <div class="translation-status">
        <div v-if="isTranslating" class="text-path">{{ progressStr }} </div>
        <div v-if="isTranslating" class="text-path"> Translating: </div>
        <div v-if="!isTranslating" class="text-path">Idle </div>
        <div class="text-path">{{ displayPath }}</div>
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
        let displayPath = computed(() => {
            let path = currentFile.value.split(/[/\\]/);
            return path[path.length - 1];
        });
        let progressStr = computed(() => {
            let progress = store.state.currentTranslation;
            return progress.thisCount + "/" + progress.totalCount;
        });
        return { isTranslating, displayPath, progressStr };
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