#!/bin/bash

# Create master_thesis/result directory if it doesn't exist
mkdir -p master_thesis/result

# Find all plots_* directories and copy .eps files
for plot_dir in plots_*/ ; do
    if [ -d "$plot_dir" ]; then
        # Get directory name without trailing slash
        dir_name="${plot_dir%/}"
        
        # Create corresponding directory in master_thesis/result
        mkdir -p "master_thesis/result/$dir_name"
        
        # Copy only white_background .eps files from this directory
        if ls "$plot_dir"*white_background.eps 1> /dev/null 2>&1; then
            cp "$plot_dir"*white_background.eps "master_thesis/result/$dir_name/"
            echo "Copied white_background .eps files from $dir_name"
        else
            echo "No white_background .eps files found in $dir_name"
        fi
    fi
done

echo "Done! EPS files copied to master_thesis/result/"
