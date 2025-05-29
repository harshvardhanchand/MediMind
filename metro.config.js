const { getDefaultConfig } = require('expo/metro-config');
const defaultConfig = getDefaultConfig(__dirname);
const path = require('path');

defaultConfig.resolver.extraNodeModules = {
  ...defaultConfig.resolver.extraNodeModules,
  buffer: require.resolve('buffer/'),
  process: require.resolve('process/browser'),
  events: require.resolve('events/'),
  util: require.resolve('util/'),
  url: require.resolve('url/'),
  stream: require.resolve('readable-stream'),
  assert: require.resolve('assert/'),
  crypto: require.resolve('crypto-browserify'),
  'readable-stream': require.resolve('readable-stream'),
  net: path.join(__dirname, 'frontend/empty.js'),
  tls: path.join(__dirname, 'frontend/empty.js'),
  fs: path.join(__dirname, 'frontend/empty.js')
};

// Ensure symlinks work
defaultConfig.resolver.disableHierarchicalLookup = true;

module.exports = defaultConfig; 