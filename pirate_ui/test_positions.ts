import WebSocket from 'ws';

const TEST_PORT = 8000;

async function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTest() {
    console.log('Starting test client...');
    const ws = new WebSocket(`ws://localhost:${TEST_PORT}`);

    ws.on('open', () => {
        console.log('Connected to server');
        sendTestData(ws);
    });

    ws.on('message', (data) => {
        console.log('Received:', JSON.parse(data.toString()));
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
}

async function sendTestData(ws: WebSocket) {
    // Initial positions
    const basePositions = {
        token_metrics: {},
        active_positions: [
            {
                token_address: '6d5zHW5B8RkGKd51Lpb9RqFQSqDudr9GJgZ1SgQZpump',
                symbol: 'AVB',
                category: 'AI',
                entry_price: 0.00145,
                current_price: 0.00152,
                tokens: 596974.67,
                r_pnl: 0,
                ur_pnl: 4.179,
                total_pnl: 4.179, // r_pnl + ur_pnl
                entry_time: new Date().toISOString()
            },
            {
                token_address: 'So11111111111111111111111111111111111111112',
                symbol: 'YUMI',
                category: 'MEME',
                entry_price: 0.00089,
                current_price: 0.00083,
                tokens: 138100.1,
                r_pnl: 0,
                ur_pnl: -8.286,
                total_pnl: -8.286, // r_pnl + ur_pnl
                entry_time: new Date().toISOString()
            },
            {
                token_address: '7mme5o7T8JgKvHX2cPYgjV8UhYCqMLhJuEskHhgc3GBp',
                symbol: 'BIP',
                category: 'AI',
                entry_price: 0.00234,
                current_price: 0.00251,
                tokens: 84776.12,
                r_pnl: 1.234,
                ur_pnl: 1.445,
                total_pnl: 2.679, // 1.234 + 1.445
                entry_time: new Date().toISOString()
            }
        ],
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

    // Send initial state
    ws.send(JSON.stringify(basePositions));
    console.log('Sent initial positions');
    await sleep(2000);

    // Simulate partial close of AVB position
    const partialClose = {
        ...basePositions,
        active_positions: [
            {
                ...basePositions.active_positions[0],
                tokens: 298487.33, // Half the tokens
                r_pnl: 5.23, // Realized profit from selling half
                current_price: 0.00153,
                ur_pnl: 2.38, // Unrealized profit on remaining tokens
                total_pnl: 7.61 // 5.23 + 2.38
            },
            basePositions.active_positions[1],
            basePositions.active_positions[2]
        ]
    };
    
    ws.send(JSON.stringify(partialClose));
    console.log('Sent partial close update');
    await sleep(2000);

    // Simulate full close of YUMI position (removed from active)
    const fullClose = {
        ...basePositions,
        active_positions: [
            partialClose.active_positions[0],
            {
                ...partialClose.active_positions[2],
                current_price: 0.00252,
                ur_pnl: 1.67,
                total_pnl: 2.904 // 1.234 + 1.67
            }
        ]
    };

    ws.send(JSON.stringify(fullClose));
    console.log('Sent full close update');
    await sleep(2000);

    // Final price updates
    const finalUpdate = {
        ...basePositions,
        active_positions: [
            {
                ...partialClose.active_positions[0],
                current_price: 0.00154,
                ur_pnl: 2.67,
                total_pnl: 7.90 // 5.23 + 2.67
            },
            {
                ...fullClose.active_positions[1],
                current_price: 0.00253,
                ur_pnl: 1.89,
                total_pnl: 3.124 // 1.234 + 1.89
            }
        ]
    };

    ws.send(JSON.stringify(finalUpdate));
    console.log('Sent final update');
}

runTest().catch(console.error);
