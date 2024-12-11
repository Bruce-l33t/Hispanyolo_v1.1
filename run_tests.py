"""
Test runner for Pirate3
Runs all tests with proper setup
"""
import pytest
import sys
import logging
from pathlib import Path

def setup_logging():
    """Setup test logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Run all tests"""
    # Setup logging
    setup_logging()
    
    # Run tests
    args = [
        # Test discovery
        'tests',
        
        # Output formatting
        '-v',
        '--tb=short',
        
        # Show local variables in tracebacks
        '--showlocals',
        
        # Show slowest tests
        '--durations=10',
        
        # Generate coverage report
        '--cov=src',
        '--cov-report=term-missing',
        
        # Parallel execution
        '-n', 'auto'
    ]
    
    return pytest.main(args)

if __name__ == '__main__':
    sys.exit(main())
