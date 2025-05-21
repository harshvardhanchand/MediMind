module.exports = global.WebSocket;

// Add basic properties to match the ws API that might be used
module.exports.Server = class Server {
  constructor() {
    throw new Error('WebSocket.Server is not supported in React Native');
  }
};

// Add any other properties that might be used from the ws package
module.exports.createWebSocketStream = () => {
  throw new Error('createWebSocketStream is not supported in React Native');
};