module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      'react-native-paper/babel',
      ["module:react-native-dotenv", {
        "moduleName": "@env",
        "path": ".env", // ensure .env is at the root of 'frontend'
        "blacklist": null,
        "whitelist": null,
        "safe": false,
        "allowUndefined": true 
      }],
      ["module-resolver", {
        "alias": {
          "stream": "stream-browserify",
          "crypto": "crypto-browserify",
          "http": "stream-http",
          "https": "https-browserify",
          "os": "os-browserify",
          "path": "path-browserify",
          "vm": "vm-browserify",
          "zlib": "browserify-zlib"
        }
      }]
    ],
  };
}; 
 