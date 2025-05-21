const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

// Find the project and workspace directories
const projectRoot = __dirname;
// This can be replaced with `find-yarn-workspace-root`
const workspaceRoot = path.resolve(projectRoot, '..');

const config = getDefaultConfig(projectRoot);

// 1. Watch all files within the monorepo
config.watchFolders = [workspaceRoot];
// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];
// 3. Force Metro to resolve (sub)dependencies only from the `nodeModulesPaths`
config.resolver.disableHierarchicalLookup = true;

// Add resolver for Node.js core modules
config.resolver.extraNodeModules = {
  
  ...(config.resolver.extraNodeModules || {}), // Preserve other aliases if they exist
  stream: require.resolve('stream-browserify'),
  crypto: require.resolve('crypto-browserify'),
  vm: require.resolve('vm-browserify'),
  url: require.resolve('url/'), // Typically available via react-native-url-polyfill
  http: require.resolve('stream-http'),
  https: require.resolve('https-browserify'),
  zlib: require.resolve('browserify-zlib'),
  os: require.resolve('os-browserify/browser'),
  path: require.resolve('path-browserify'),
};

module.exports = config; 