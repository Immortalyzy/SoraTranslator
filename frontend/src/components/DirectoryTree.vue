<template>
  <div class="container-directory-tree">
    <div class="title">
      {{ titleInfo }}
      <hr />
    </div>
    <div class="directory-tree" v-for="(value, name) in treeData" :key="name">
      <div class="folder-name">{{ name }}</div>
      <div class="folder-contents" v-if="isObject(value)">
        <tree-folder :tree-data="value" />
      </div>
      <div class="file-name" v-else>
        <h2>Please select a project.</h2>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "DirectoryTree",
  props: {
    currentTreeDisplay: {
      type: String,
      default: "S"
    },
  },
  data() {
  },
  computed: {
    titleInfo() {
      if (this.currentTreeDisplay === "S") {
        return "Script Files:";
      } else if (this.currentTreeDisplay === "T") {
        return "Text Files:";
      } else if (this.currentTreeDisplay === "R") {
        return "Result Files:";
      }
      alert(this.currentTreeDisplay)
      return "Tree Display";
    }


  },
  methods: {
  }
};
</script>

<style>
.container-directory-tree {
  display: flex;
  flex-direction: column;
}

.title {
  color: white;
  font-size: large;
  font-weight: bold;
  flex-basis: 5%;
  align-items: center;
  vertical-align: middle;
  padding: 0 0;
  margin: 0px 0px;
}

.directory-tree {
  margin-left: 00px;
}

.folder-name {
  font-weight: bold;
}
</style>
