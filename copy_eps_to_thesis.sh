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

# Create intermediate directory
mkdir -p master_thesis/result/intermediate

# Copy specific trajectory files with system names removed
declare -A files_to_copy=(
    ["damping_zero_force_nonzero_cart_pole"]="cart_pole"
    ["damping_nonzero_force_zero_double_pendulum_pm"]="double_pendulum_pm"
    ["damping_nonzero_force_nonzero_cart_pole"]="cart_pole"
    ["damping_nonzero_force_mixed_cart_pole_double"]="cart_pole_double"
)

for file_pattern in "${!files_to_copy[@]}"; do
    system_name="${files_to_copy[$file_pattern]}"
    
    # Copy _white.eps files
    if [ -f "plots/${file_pattern}_white.eps" ]; then
        new_name="${file_pattern/_${system_name}/}"
        cp "plots/${file_pattern}_white.eps" "master_thesis/result/intermediate/${new_name}_white.eps"
        echo "Copied ${file_pattern}_white.eps -> ${new_name}_white.eps"
    fi
    
    # Copy .tex files
    if [ -f "plots/${file_pattern}.tex" ]; then
        new_name="${file_pattern/_${system_name}/}"
        cp "plots/${file_pattern}.tex" "master_thesis/result/intermediate/${new_name}.tex"
        echo "Copied ${file_pattern}.tex -> ${new_name}.tex"
    fi
done

echo "Intermediate files copied to master_thesis/result/intermediate/"
