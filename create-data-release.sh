#!/bin/bash

# Create GitHub Release with Data
# This script packages data and creates a GitHub release automatically

set -e

# Configuration
RESULTS_DIR="results"
RESULTS_DATA_DIR="results_data"
OUTPUT_DIR="data-archive"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Creating GitHub Release with Data${NC}"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo -e "${YELLOW}📦 Install it with:${NC}"
    echo "  Ubuntu/Debian: sudo apt install gh"
    echo "  macOS: brew install gh"
    echo "  Or download from: https://github.com/cli/cli/releases"
    echo ""
    echo -e "${YELLOW}🔑 Then authenticate with: gh auth login${NC}"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo -e "${YELLOW}🔑 Run: gh auth login${NC}"
    exit 1
fi

# Get version from user or auto-increment
if [ -z "$1" ]; then
    # Auto-increment version based on latest release
    LATEST_TAG=$(gh release list --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null | grep '^data-' || echo "")
    if [ -n "$LATEST_TAG" ]; then
        # Extract version number and increment
        VERSION_NUM=$(echo "$LATEST_TAG" | sed 's/data-v//' | awk -F. '{print $1"."$2"."($3+1)}')
        TAG_NAME="data-v$VERSION_NUM"
    else
        TAG_NAME="data-v1.0.0"
    fi
    echo -e "${BLUE}🏷️  Auto-generated tag: $TAG_NAME${NC}"
else
    TAG_NAME="$1"
    if [[ ! "$TAG_NAME" =~ ^data-v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${YELLOW}⚠️  Tag should follow format: data-vX.Y.Z${NC}"
        echo -e "${YELLOW}   Using provided tag: $TAG_NAME${NC}"
    fi
fi

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

# Clean up previous archives
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Get timestamp for file naming
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${YELLOW}📦 Packaging data files...${NC}"

# Package JSON results
if [ -d "$RESULTS_DIR" ]; then
    json_count=$(find "$RESULTS_DIR" -name "*.json" | wc -l)
    if [ $json_count -gt 0 ]; then
        echo -e "   📄 Packaging $json_count JSON files..."
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
        echo -e "   📊 Packaging $data_count data files..."
        cd "$RESULTS_DATA_DIR"
        tar -czf "../$OUTPUT_DIR/results-data-$TIMESTAMP.tar.gz" *
        cd ..
        echo -e "${GREEN}   ✓ Created: results-data-$TIMESTAMP.tar.gz${NC}"
    fi
fi

# Create manifest
echo -e "${YELLOW}📋 Creating manifest...${NC}"
{
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"tag\": \"$TAG_NAME\","
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
    echo "  ]"
    echo "}"
} > "$OUTPUT_DIR/manifest.json"

# Check if we have files to upload
UPLOAD_FILES=()
for file in "$OUTPUT_DIR"/*; do
    if [ -f "$file" ]; then
        UPLOAD_FILES+=("$file")
    fi
done

if [ ${#UPLOAD_FILES[@]} -eq 0 ]; then
    echo -e "${RED}❌ No files to upload${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Files ready for release:${NC}"
ls -lh "$OUTPUT_DIR"

# Create the release
echo -e "${YELLOW}🚀 Creating GitHub release: $TAG_NAME${NC}"

RELEASE_NOTES="# Result Data Release $TAG_NAME

Generated on: $(date)
Archives: ${#UPLOAD_FILES[@]} files

## Contents
- JSON result files (compressed)
- Binary data files (compressed) 
- Manifest with file information

## Usage
This data will be automatically downloaded and included during site deployment.

## Download URLs
Files are available at:
\`https://github.com/Eymeric65/py-xl-sindy-data-visualisation/releases/download/$TAG_NAME/[filename]\`"

# Create release and upload files
gh release create "$TAG_NAME" \
    --title "Result Data $TAG_NAME" \
    --notes "$RELEASE_NOTES" \
    "${UPLOAD_FILES[@]}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Release created successfully!${NC}"
    echo -e "${GREEN}🌐 View at: https://github.com/Eymeric65/py-xl-sindy-data-visualisation/releases/tag/$TAG_NAME${NC}"
    echo ""
    echo -e "${BLUE}🔄 Next steps:${NC}"
    echo "1. Push any code changes to trigger deployment"
    echo "2. The deployment will automatically download this data"
    echo "3. Your site will be built with the latest data included"
    
    # Clean up
    echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
    rm -rf "$OUTPUT_DIR"
    
else
    echo -e "${RED}❌ Failed to create release${NC}"
    exit 1
fi