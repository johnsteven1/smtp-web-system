#!/bin/bash

echo "========================================="
echo "📧 SMTP Web System - Starting..."
echo "========================================="

# Get local IP
LOCAL_IP=$(ip addr show wlan0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo ""
echo "🌐 Access the web interface:"
echo "   Local: http://localhost:5000"
echo "   Network: http://$LOCAL_IP:5000"
echo ""
echo "🔑 Default login password: admin123"
echo ""
echo "⚠️  IMPORTANT: Update email credentials in config/email_accounts.json"
echo "========================================="

# Run the application
python app.py
