#!/bin/bash
# Quick Start Guide for Canary File Tripwire System
# =====================================================

# This script demonstrates the complete workflow of Canary

echo "=========================================="
echo "CANARY FILE TRIPWIRE - QUICK START"
echo "=========================================="
echo

# Step 1: Activate virtual environment
echo "[STEP 1] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo

# Step 2: Initialize Canary
echo "[STEP 2] Initializing Canary..."
canary init
echo

# Step 3: Add files to monitor
echo "[STEP 3] Adding files to monitor..."
canary add /etc/passwd
canary add /etc/sudoers
echo

# Step 4: List monitored files
echo "[STEP 4] Listing monitored files..."
canary list
echo

# Step 5: Set webhook (optional)
echo "[STEP 5] Configuring webhook..."
echo "Note: In production, use your actual webhook URL"
canary set-webhook https://webhook.site/your-unique-id
echo

# Step 6: View configuration
echo "[STEP 6] Configuration file contents:"
echo "Location: ~/.canary/config.json"
echo "---"
cat ~/.canary/config.json
echo "---"
echo

# Step 7: Start monitoring (with timeout for demo)
echo "[STEP 7] Starting file monitoring..."
echo "Note: In production, run 'canary watch' directly"
echo "This demo will run for 10 seconds with timeout..."
timeout 10 canary watch || true
echo

echo "=========================================="
echo "✓ CANARY QUICKSTART COMPLETE"
echo "=========================================="
echo "For more information, see README.md"
