// vue.config.js
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    node: {
      __dirname: true,
      __filename: true,
    },
    resolve: {
      fallback: {
        fs: false,
        path: require.resolve("path-browserify"),
      },
    },
  },
  pluginOptions: {
    electronBuilder: {
      preload: 'src/preload.js',
      // 👇 ADD THIS BLOCK
      builderOptions: {
        appId: 'com.yourdomain.soratranslator',
        productName: 'Sora Translator',
        asar: true,
        directories: {
          output: 'dist_electron'
        },
        files: [
          '**/*'
        ],
        extraMetadata: {
          // Keep Electron main entry as the plugin outputs it
          main: 'background.js'
        },
        // ---- Windows
        win: {
          target: [{ target: 'nsis', arch: ['x64', 'arm64'] }],
          icon: 'build/icons/icon.ico',
          artifactName: '${productName}-${version}-Setup-${arch}.${ext}'
        },
        nsis: {
          oneClick: false,
          allowElevation: true,
          allowToChangeInstallationDirectory: true,
          createDesktopShortcut: true,
          createStartMenuShortcut: true
        },
        // ---- macOS
        mac: {
          target: ['dmg'],
          category: 'public.app-category.productivity',
          icon: 'build/icons/icon.icns',
          hardenedRuntime: false // set true when you’re ready to sign/notarize
        },
        dmg: {
          background: null
        },
        // ---- Linux
        linux: {
          target: ['AppImage', 'deb'],
          icon: 'build/icons',
          category: 'Utility'
        }
      }
    }
  }
})
