#!/bin/bash

# Local development build script for py-xl-sindy-data-visualisation
# This script builds the site with local development configuration

echo "Building for local development..."

# Use the dev config for local builds
yarn build --config vite.config.dev.ts

echo "Local build complete! Files are in dist/"
echo "You can serve locally with: yarn preview"