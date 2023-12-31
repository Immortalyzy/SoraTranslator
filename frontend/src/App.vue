<template>
  <div id="app">
    <header class="app-header">
      <img src="./assets/logo.png" class="app-logo" alt="logo" />
      <h1 class="app-title">SoraTranslator</h1>
      <MenuBar @change-display-type="changeDisplay" />
    </header>
    <div class="main-content">
      <SideBar class="side-bar" @change-tree="changeTree" @show-tree="showTree" />
      <DirectoryTree :currentTreeDisplay="treeDisplay" @change-display="changeDisplay" class="directory-tree" />
      <MainDisplay :displayType="displayType" :filePath="filePath" class="file-display" @change-display="changeDisplay" />
      <ActionInfo class="action-info" />
    </div>
    <StatusBar :message="statusMessage" class="status-bar" />
    <div class="background">
      <div class="color-overlay">
      </div>
    </div>
  </div>
</template>

<script>
import MenuBar from './components/MenuBar.vue';
import MainDisplay from './components/MainDisplay.vue';
import StatusBar from './components/StatusBar.vue';
import ActionInfo from './components/ActionInfo.vue';
import DirectoryTree from './components/DirectoryTree.vue';
import SideBar from './components/SideBar.vue';

export default {
  name: 'App',
  components: {
    MenuBar,
    StatusBar,
    MainDisplay,
    ActionInfo,
    DirectoryTree,
    SideBar

  },
  data() {
    return {
      // possible types : new_project, game, package, script, text
      displayType: "new_project",
      filePath: 'DISPLAY OF TEXT',
      statusMessage: 'STATUS',
      treeDisplay: 'S',
      showTreeDisplay: true
    };
  },
  methods: {
    displayFile(content) {
      this.fileContent = content;
      this.statusMessage = 'Displaying content...';
    },
    changeTree(letter) {
      this.treeDisplay = letter;
      this.statusMessage = 'Changing tree display to ' + letter;
    },
    showTree(if_show) {
      this.showTreeDisplay = if_show;
      if (if_show) {
        this.statusMessage = 'Showing tree display';
      } else {
        this.statusMessage = 'Hiding tree display';
      }
    },
    changeDisplay(type, pathToFile) {
      this.displayType = type;
      this.filePath = pathToFile;
      this.statusMessage = 'Changing display to ' + type + ' at ' + pathToFile;
      this.$store.dispatch("updateCurrentDisplay", { type: type, filePath: pathToFile });
    }

  }
};
</script>


<style>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Amatic+SC&display=swap');

html,
body {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.background {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-image: url('~@/assets/sora.png');
  background-size: cover;
  background-position: center;
  opacity: 1;
  z-index: -2;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
}

.color-overlay {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgb(49, 33, 33);
  z-index: -1;
  opacity: 0.7;
  pointer-events: none;

}

.main-content {
  display: flex;
  flex-direction: row;
  width: 100vw;
}

.main-content>* {
  height: calc(100vh - 55px - 70px);
  flex-shrink: 0;
  flex-grow: 0;
  margin: 0 0;
  background-color: rgba(0, 0, 0, 0.103);
  border: 3px solid rgb(71, 0, 0);
  box-sizing: border-box;
}

.side-bar {
  flex-basis: 2vw;

}

.directory-tree {
  flex-basis: 13%;
  max-width: 13%;
}

.file-display {
  flex-basis: 70%;
  max-width: 70%;
}

.action-info {
  flex-basis: 15%;
}

.status-bar {
  width: 100vw;
  height: 70px;
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
}

.app-header {
  text-align: left;
  align-items: top;
  display: flex;
  width: 100vw;
  height: 55px;
  align-items: top;
  vertical-align: top;
  padding: 0px 0;
  margin: 0px 0;
  border: rgb(75, 0, 0);
}

.app-title {
  text-align: left;
  align-items: top;
  vertical-align: top;
  font-size: 40px;
  font-family: 'Amatic SC', cursive;
  color: #ffffff;
  margin: 0px 0;
  padding: 0px;
  text-shadow: 0 0 10px rgba(255, 200, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
  /* Red glow */
}

.app-logo {
  height: 50px;
  margin: 0px 0;
  padding: 0px 0;
  animation: app-logo-spin infinite 20s linear;
}
</style>
