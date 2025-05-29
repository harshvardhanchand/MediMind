import { Buffer } from 'buffer';
import 'react-native-polyfill-globals/auto';
import 'react-native-get-random-values';

// Polyfill globals
global.Buffer = Buffer;
global.process = require('process');

// Set up environment
global.process.env = process.env || {};
global.process.version = ''; // Node.js version
global.process.versions = { node: '' };

// Stream polyfill
const { Readable } = require('readable-stream');
global.Stream = Readable;
global.stream = require('readable-stream');

// Use React Native's native WebSocket implementation
if (typeof global.WebSocket === 'undefined') {
  // React Native already provides a global WebSocket
  global.WebSocket = WebSocket;
} 