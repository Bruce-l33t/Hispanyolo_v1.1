#!/usr/bin/env python3
"""
Whale Hunter Trading System
Entry point script that runs the system from the src package
"""

import asyncio
import logging
from src.main import main

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger('main')
    
    try:
        logger.info("Starting Whale Hunter Trading System...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
