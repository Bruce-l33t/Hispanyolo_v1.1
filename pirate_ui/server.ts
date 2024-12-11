import { WebSocketServer, WebSocket } from 'ws';
import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join } from 'path';

// Create HTTP server
const server = createServer((req, res) => {
  if (req.url === '/') {
    const html = readFileSync(join(__dirname, 'index.html'), 'utf8');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
  }
  else if (req.url === '/formatting.js') {
    const js = readFileSync(join(__dirname, 'formatting.js'), 'utf8');
    res.writeHead(200, { 'Content-Type': 'application/javascript' });
    res.end(js);
  }
});

// Create WebSocket server
const wss = new WebSocketServer({ server });

// Store connected clients
const clients = new Set<WebSocket>();

// Current state
let currentState = {
  token_metrics: {},
  active_positions: [],  // Changed from positions object to array
  recent_transactions: [],
  wallet_status: {
    VERY_ACTIVE: 0,
    ACTIVE: 0,
    WATCHING: 0,
    ASLEEP: 0
  },
  wallets_checked: 0,
  transactions_processed: 0,
  start_time: new Date().toISOString()
};

function heartbeat(this: WebSocket) {
  (this as any).isAlive = true;
}

// Handle WebSocket connections
wss.on('connection', (ws: WebSocket) => {
  console.log('Client connected');
  (ws as any).isAlive = true;
  clients.add(ws);

  // Handle pong messages
  ws.on('pong', heartbeat);

  // Send initial state
  ws.send(JSON.stringify(currentState));

  // Handle incoming messages
  ws.on('message', (message: string) => {
    try {
      const data = JSON.parse(message.toString());
      console.log('Received update:', Object.keys(data));

      // Handle position updates
      if (data.active_positions) {
        console.log('\nPosition update:');
        console.log('New positions:', data.active_positions.length);
        currentState.active_positions = data.active_positions;
      }
      
      // Handle token metrics updates
      else if (data.token_metrics) {
        console.log('\nToken metrics update:');
        console.log('Current metrics:', Object.keys(currentState.token_metrics).length, 'tokens');
        console.log('New metrics:', Object.keys(data.token_metrics).length, 'tokens');
        
        currentState.token_metrics = {
          ...currentState.token_metrics,
          ...data.token_metrics
        };
      }
      
      // Handle other updates
      else {
        currentState = {
          ...currentState,
          ...data
        };
      }

      // Broadcast the update to all clients
      broadcast(currentState);
    } catch (error) {
      console.error('Error processing message:', error);
      console.error('Raw message:', message.toString());
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
    clients.delete(ws);
  });
});

// Broadcast updates to all clients
function broadcast(data: any) {
  const message = JSON.stringify(data);
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  }
}

// Ping clients every 30 seconds
const interval = setInterval(() => {
  wss.clients.forEach((ws) => {
    if ((ws as any).isAlive === false) {
      console.log('Terminating inactive client');
      return ws.terminate();
    }
    
    (ws as any).isAlive = false;
    ws.ping();
  });
}, 30000);

wss.on('close', () => {
  clearInterval(interval);
});

// Start server
const PORT = 8000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Export for external use
export { broadcast };
