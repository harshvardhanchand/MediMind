const createExpoWebpackConfigAsync = require('@expo/webpack-config');
const path = require('path');

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(
    {
      ...env,
      babel: {
        dangerouslyAddModulePathsToTranspile: [
          // Add any packages that need transpiling here
        ],
      },
    },
    argv
  );

  // Customize the config before returning it
  config.resolve.alias = {
    ...config.resolve.alias,
    // Add any custom aliases here
  };

  // Add fallbacks for Node.js core modules
  config.resolve.fallback = {
    ...config.resolve.fallback,
    "crypto": require.resolve("crypto-browserify"),
    "stream": require.resolve("stream-browserify"),
    "vm": require.resolve("vm-browserify"),
  };

  return config;
}; 