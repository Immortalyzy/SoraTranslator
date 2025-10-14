set http_proxy=http://127.0.0.1:10809
set https_proxy=http://127.0.0.1:10809
set NODE_OPTIONS=--openssl-legacy-provider
yarn run electron:build -- --win nsis