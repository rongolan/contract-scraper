#!/bin/bash

# Cron script for running the contract scraper
# This script ensures proper environment and logging

# Set the working directory
cd /Users/rongolan/Desktop/contract_scraper

# Log when cron starts
echo "cron fired at $(date)" >> cron.log

# Activate virtual environment and run orchestrator
source venv/bin/activate

# Set Python path to avoid import issues
export PYTHONPATH="/Users/rongolan/Desktop/contract_scraper:$PYTHONPATH"

# Run the orchestrator with full output logged
python orchestrator.py >> cron.log 2>&1

# Log completion
echo "cron completed at $(date)" >> cron.log
echo "---" >> cron.log