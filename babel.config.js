module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      'react-native-paper/babel',
      'nativewind/babel',
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
 