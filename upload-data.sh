#!/bin/bash

# Create Data Archive for GitHub Release
# This script packages your local resulecho ""
echo -e "${YELLOW}🚀 Next steps:${NC}"
echo "1. Create a GitHub Release:"
echo "   - Go to: https://github.com/Eymeric65/py-xl-sindy-data-visualisation/releases"
echo "   - Click 'Create a new release'"
echo "   - Tag: 'data-v1.0.0' (or increment version)"
echo "   - Title: 'Result Data v1.0.0'"
echo "   - Upload the files from $OUTPUT_DIR/ as release assets"
echo ""
echo "2. The deployment workflow will automatically:"
echo "   - Download the latest data release"
echo "   - Extract files and include them in the site build"
echo "   - Deploy to GitHub Pages with the data included"
echo ""
echo -e "${GREEN}🔄 The app stays clean - data is fetched at build time!${NC}"nto archives ready for upload

set -e

# Configuration
RESULTS_DIR="results"
RESULTS_DATA_DIR="results_data"
OUTPUT_DIR="data-archive"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}� Creating Data Archive for GitHub Release${NC}"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "site" ]; then
    echo -e "${RED}❌ Please run this script from the repository root${NC}"
    exit 1
fi

# Check if result directories exist
if [ ! -d "$RESULTS_DIR" ] && [ ! -d "$RESULTS_DATA_DIR" ]; then
    echo -e "${RED}❌ No result directories found ($RESULTS_DIR or $RESULTS_DATA_DIR)${NC}"
    echo "Please make sure your result data is available locally"
    exit 1
fi

# Create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Get timestamp for file naming
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Package JSON results
if [ -d "$RESULTS_DIR" ]; then
    json_count=$(find "$RESULTS_DIR" -name "*.json" | wc -l)
    if [ $json_count -gt 0 ]; then
        echo -e "${YELLOW}📄 Packaging $json_count JSON files...${NC}"
        cd "$RESULTS_DIR"
        tar -czf "../$OUTPUT_DIR/results-json-$TIMESTAMP.tar.gz" *.json
        cd ..
        echo -e "${GREEN}   ✓ Created: results-json-$TIMESTAMP.tar.gz${NC}"
    fi
fi

# Package data files separately
if [ -d "$RESULTS_DATA_DIR" ]; then
    data_count=$(find "$RESULTS_DATA_DIR" -type f | wc -l)
    if [ $data_count -gt 0 ]; then
        echo -e "${YELLOW}📊 Packaging $data_count data files...${NC}"
        tar -czf "$OUTPUT_DIR/results-data-$TIMESTAMP.tar.gz" -C "$RESULTS_DATA_DIR" .
        echo -e "${GREEN}   ✓ Created: results-data-$TIMESTAMP.tar.gz${NC}"
    fi
fi

# Create manifest
echo -e "${YELLOW}📋 Creating manifest...${NC}"
{
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"archives\": ["
    first=true
    for archive in "$OUTPUT_DIR"/*.tar.gz; do
        if [ -f "$archive" ]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            filename=$(basename "$archive")
            size=$(stat -c%s "$archive")
            echo -n "    {\"name\": \"$filename\", \"size\": $size}"
        fi
    done
    echo ""
    echo "  ],"
    echo "  \"usage\": {"
    echo "    \"download_url\": \"https://github.com/Eymeric65/py-xl-sindy-data-visualisation/releases/download/[TAG]/[FILENAME]\","
    echo "    \"instructions\": \"Upload these archives to a GitHub Release and use the download URLs in your app\""
    echo "  }"
    echo "}"
} > "$OUTPUT_DIR/manifest.json"

# Summary
echo -e "${GREEN}✅ Data archives created in $OUTPUT_DIR/${NC}"
echo -e "${GREEN}📦 Files ready for upload:${NC}"
ls -lh "$OUTPUT_DIR"

echo ""
echo -e "${YELLOW}🚀 Next steps:${NC}"
echo "1. Create a GitHub Release (or run the package-data.yml workflow)"
echo "2. Upload the files from $OUTPUT_DIR/ as release assets"
echo "3. Update your React app to fetch from the release URLs"
echo ""
echo -e "${GREEN}� Release URL format:${NC}"
echo "https://github.com/Eymeric65/py-xl-sindy-data-visualisation/releases/download/[TAG]/[FILENAME]"