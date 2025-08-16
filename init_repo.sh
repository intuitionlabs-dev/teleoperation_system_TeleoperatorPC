#!/bin/bash
# Initialize and prepare teleoperation-client repo

echo "Initializing teleoperation-client repository..."

# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Minimal teleoperation client for GELLO control"

echo ""
echo "Repository initialized! To push to GitHub:"
echo ""
echo "1. Create repo at: https://github.com/orgs/intuitionlabs-dev/repositories"
echo "   Name: teleoperation-client"
echo "   Description: Minimal ZMQ client for bimanual robot teleoperation"
echo ""
echo "2. Then run:"
echo "   git remote add origin https://github.com/intuitionlabs-dev/teleoperation-client.git"
echo "   git branch -M main"
echo "   git push -u origin main"
