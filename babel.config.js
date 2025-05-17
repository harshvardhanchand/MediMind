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
      }]
    ],
  };
}; 
 