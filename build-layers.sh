#!/bin/bash
set -e

echo "🔨 Building Lambda Layers"
echo "========================="

# Clean previous builds
rm -rf layers/
mkdir -p layers/python-libraries/python
mkdir -p layers/salesforce-libraries/python

# Build python-libraries layer
echo "Building python-libraries layer..."
pip3 install -q \
    requests==2.31.0 \
    phonenumbers==8.13.26 \
    wrapt==1.16.0 \
    -t layers/python-libraries/python/

# Build salesforce-libraries layer
echo "Building salesforce-libraries layer..."
pip3 install -q \
    simple-salesforce==1.12.5 \
    PyJWT==2.8.0 \
    cryptography==41.0.7 \
    -t layers/salesforce-libraries/python/

# Clean up unnecessary files
echo "Cleaning up..."
find layers/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find layers/ -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find layers/ -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✓ Layers built successfully"
echo "  python-libraries: $(du -sh layers/python-libraries | cut -f1)"
echo "  salesforce-libraries: $(du -sh layers/salesforce-libraries | cut -f1)"
