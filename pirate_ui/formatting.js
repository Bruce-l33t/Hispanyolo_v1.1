// Formatting utilities for Pirate UI

// Format numbers with proper decimal places for token amounts
function formatNumber(num) {
    if (num === undefined || num === null) return '0.0000';
    return Number(num).toFixed(10);  // Keep full precision for tokens
}

// Format price values in SOL with leading zero notation
function formatPrice(price) {
    if (!price) return '0.0000 SOL';
    
    // Convert to string and handle scientific notation
    let str = price.toString();
    if (str.includes('e-')) {
        // Convert scientific notation to decimal
        const [base, exponent] = str.split('e-');
        str = '0.' + '0'.repeat(Number(exponent) - 1) + base.replace('.', '');
    }
    
    // Count leading zeros after decimal (up to 13)
    const match = str.match(/\.0*/);
    if (!match) return `${Number(price).toFixed(4)} SOL`;  // No leading zeros
    
    const zeros = Math.min(match[0].length - 1, 13);  // Cap at 13 zeros, subtract 1 for decimal
    const significantDigits = str.replace(/^0\.0*/, '').substring(0, 13);  // Limit significant digits
    
    return `0.(${zeros})${significantDigits} SOL`;
}

/* Test cases:
console.log(formatPrice(0.0000000000001));  // 0.(12)1 SOL
console.log(formatPrice(0.0000000000123));  // 0.(11)123 SOL
console.log(formatPrice(0.0000000001234));  // 0.(9)1234 SOL
console.log(formatPrice(0.0000012345678));  // 0.(6)12345678 SOL
console.log(formatPrice(0.0123456789012));  // 0.(2)123456789012 SOL
console.log(formatPrice(1.234567890123));   // 1.2345 SOL
*/

// Format percentage values
function formatPercentage(value) {
    if (value === undefined || value === null) return '0.00%';
    return `${(value * 100).toFixed(2)}%`;
}

// Get emoji for token category
function getTokenEmoji(category) {
    switch (category) {
        case 'AI': return '🤖';
        case 'MEME': return '😊';
        default: return '🪙';
    }
}
