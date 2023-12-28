const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      fallback: {
        fs: false, // Tell webpack not to polyfill 'fs'
        path: false,// Add other Node modules here if necessary
      }
    }
  },
  pluginOptions: {
    electronBuilder: {
      preload: 'src/preload.js'
    }
  }
})
