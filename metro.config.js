const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const frontendRoot = path.resolve(projectRoot, 'frontend');

const config = getDefaultConfig(projectRoot);

// Watch the entire workspace
config.watchFolders = [projectRoot];

// Configure node modules resolution
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
];

// Configure resolver for Node.js core modules and polyfills
config.resolver.extraNodeModules = {
  ...(config.resolver.extraNodeModules || {}),
  buffer: require.resolve('buffer/'),
  process: require.resolve('process/browser'),
  events: require.resolve('events/'),
  util: require.resolve('util/'),
  url: require.resolve('url/'),
  stream: require.resolve('readable-stream'),
  assert: require.resolve('assert/'),
  crypto: require.resolve('crypto-browserify'),
  'readable-stream': require.resolve('readable-stream'),
  net: path.join(frontendRoot, 'empty.js'),
  tls: path.join(frontendRoot, 'empty.js'),
  fs: path.join(frontendRoot, 'empty.js'),
  ws: path.resolve(frontendRoot, 'shims/ws.js'),
};

// Force Metro to resolve dependencies only from nodeModulesPaths
config.resolver.disableHierarchicalLookup = true;

module.exports = config; 