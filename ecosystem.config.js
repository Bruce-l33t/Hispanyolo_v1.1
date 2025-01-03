module.exports = {
  apps: [
    {
      name: 'pirate-backend',
      script: 'run.py',
      interpreter: './venv/bin/python',
      env: {
        PYTHONPATH: '.'
      }
    }
  ]
} 