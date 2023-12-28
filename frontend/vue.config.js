const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    node: {
      __dirname: true, // Preserve the __dirname behavior
      __filename: true, // Aodd this if you need __filename as well
    },
    resolve: {
      fallback: {
        fs: false,
        //        path: false,// Add other Node modules here if necessary
        "path": require.resolve("path-browserify")
      }
    }
  },
  pluginOptions: {
    electronBuilder: {
      preload: 'src/preload.js'
    }
  }
})
