const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})

module.exports = {
  configureWebpack: {
    resolve: {
      fallback: {
        fs: false, // Tell webpack not to polyfill 'fs'
        // Add other Node modules here if necessary
      }
    }
  }
}