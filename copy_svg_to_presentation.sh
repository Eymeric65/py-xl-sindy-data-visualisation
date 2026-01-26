#!/bin/bash

# Base directories
SOURCE_ROOT="/home/eymeric/py-xl-sindy-data-visualisation"
DEST_ROOT="$SOURCE_ROOT/presentation/manim_project/image/results"

# Create destination root if it doesn't exist
mkdir -p "$DEST_ROOT"

# Find all directories starting with "plots" in the root
for plots_dir in "$SOURCE_ROOT"/plots*; do
    # Check if it's a directory
    if [ -d "$plots_dir" ]; then
        # Get the folder name (e.g., "plots", "plots_damping_explicit")
        folder_name=$(basename "$plots_dir")
        
        echo "Processing $folder_name..."
        
        # Create the destination folder
        dest_folder="$DEST_ROOT/$folder_name"
        mkdir -p "$dest_folder"
        
        # Find and copy all .svg files, preserving directory structure
        find "$plots_dir" -type f -name "*.svg" | while read svg_file; do
            # Get the relative path from the plots_dir
            relative_path="${svg_file#$plots_dir/}"
            
            # Get the directory part of the relative path
            relative_dir=$(dirname "$relative_path")
            
            # Create the destination directory structure
            if [ "$relative_dir" != "." ]; then
                mkdir -p "$dest_folder/$relative_dir"
            fi
            
            # Copy the file
            cp "$svg_file" "$dest_folder/$relative_path"
            echo "  Copied: $relative_path"
        done
        
        echo "Finished processing $folder_name"
        echo ""
    fi
done

echo "All plots folders and SVG files have been copied to $DEST_ROOT"
