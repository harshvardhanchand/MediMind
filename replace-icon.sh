#!/bin/bash

# Check if source icon exists
if [ ! -f "$1" ]; then
    echo "Usage: ./replace-icon.sh <path-to-your-heartbeat-icon.png>"
    echo "Please provide your heartbeat icon file"
    exit 1
fi

SOURCE_ICON="$1"

# Create icon.png (1024x1024)
convert "$SOURCE_ICON" -resize 1024x1024 "frontend/assets/icon.png"
echo "✅ Created icon.png"

# Create splash-icon.png (same as icon)
convert "$SOURCE_ICON" -resize 1024x1024 "frontend/assets/splash-icon.png"
echo "✅ Created splash-icon.png"

# Create adaptive-icon.png (with padding for Android)
convert "$SOURCE_ICON" -resize 800x800 -background transparent -gravity center -extent 1024x1024 "frontend/assets/adaptive-icon.png"
echo "✅ Created adaptive-icon.png (with padding for Android)"

echo ""
echo "🎉 All icons have been replaced with your heartbeat icon!"
echo "📱 Your app will now use the medical heartbeat icon" 