import { WebSocket, WebSocketServer } from 'ws';
import { createServer } from 'http';
import { EventEmitter } from 'events';

interface Position {
    token_address: string;
    symbol: string;
    category: string;
    entry_price: number;
    current_price: number;
    tokens: number;
    entry_time: string;
    r_pnl: number;
    ur_pnl: number;
    status: string;
    take_profits: number[];
    profit_levels_hit: number[];
}

interface SystemState {
    positions: { [key: string]: Position };
    token_metrics: any;
    wallet_status: any;
    wallets_checked: number;
    transactions_processed: number;
    recent_transactions: any[];
}

class UIServer {
    private wss: WebSocketServer;
    private clients: Set<WebSocket>;
    private state: SystemState;
    private eventEmitter: EventEmitter;
    private reconnectTimeouts: Map<WebSocket, NodeJS.Timeout>;

    constructor() {
        const server = createServer();
        this.wss = new WebSocketServer({ server });
        this.clients = new Set();
        this.reconnectTimeouts = new Map();
        this.eventEmitter = new EventEmitter();
        
        // Initialize state
        this.state = {
            positions: {},
            token_metrics: {},
            wallet_status: {},
            wallets_checked: 0,
            transactions_processed: 0,
            recent_transactions: []
        };
        
        this.setupWebSocket();
        server.listen(8000);
    }

    private setupWebSocket() {
        this.wss.on('connection', (ws: WebSocket) => {
            console.log('Client connected');
            this.clients.add(ws);
            
            // Send full state on connection
            this.sendFullState(ws);
            
            ws.on('message', (message: string) => {
                try {
                    const data = JSON.parse(message.toString());
                    if (data.type === 'request_full_state') {
                        this.sendFullState(ws);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            });
            
            ws.on('close', () => {
                console.log('Client disconnected');
                this.clients.delete(ws);
                
                // Clear any existing reconnect timeout
                const timeout = this.reconnectTimeouts.get(ws);
                if (timeout) {
                    clearTimeout(timeout);
                    this.reconnectTimeouts.delete(ws);
                }
            });
            
            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.handleError(ws);
            });
        });
    }
    
    private handleError(ws: WebSocket) {
        // Remove client and attempt reconnect
        this.clients.delete(ws);
        
        // Clear any existing reconnect timeout
        const existingTimeout = this.reconnectTimeouts.get(ws);
        if (existingTimeout) {
            clearTimeout(existingTimeout);
        }
        
        // Set new reconnect timeout
        const timeout = setTimeout(() => {
            if (ws.readyState === WebSocket.CLOSED) {
                ws.close();
                this.reconnectTimeouts.delete(ws);
            }
        }, 5000);
        
        this.reconnectTimeouts.set(ws, timeout);
    }
    
    private sendFullState(ws: WebSocket) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'full_state',
                data: this.state
            }));
        }
    }
    
    private broadcast(data: any) {
        const message = JSON.stringify(data);
        for (const client of this.clients) {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        }
    }
    
    public updatePositions(positions: { [key: string]: Position }) {
        this.state.positions = positions;
        this.broadcast({ positions });
    }
    
    public updateTokenMetrics(metrics: any) {
        this.state.token_metrics = metrics;
        this.broadcast({ token_metrics: metrics });
    }
    
    public updateWalletStatus(status: any) {
        this.state.wallet_status = status;
        this.broadcast({ wallet_status: status });
    }
    
    public updateSystemMetrics(metrics: { 
        wallets_checked: number;
        transactions_processed: number;
    }) {
        this.state.wallets_checked = metrics.wallets_checked;
        this.state.transactions_processed = metrics.transactions_processed;
        this.broadcast({ 
            wallets_checked: metrics.wallets_checked,
            transactions_processed: metrics.transactions_processed
        });
    }
    
    public addTransaction(transaction: any) {
        this.state.recent_transactions.unshift(transaction);
        this.state.recent_transactions = this.state.recent_transactions.slice(0, 50);
        this.broadcast({ 
            recent_transactions: this.state.recent_transactions 
        });
    }
}

export const uiServer = new UIServer();
