#!/usr/bin/env python3
"""
Generate mustache (box) plots comparing validation errors across different combinations.

Creates ONE plot combining ALL systems, with noise levels as columns.
Each subplot shows box plots comparing the three combinations:
- (mixed, mixed)
- (xlsindy, explicit)
- (sindy, explicit)

All systems are mixed together in each subplot.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def load_data(csv_path: str) -> dict:
    """
    Load validation errors from the database.
    
    Returns:
        Dictionary: {noise_level: {combo: [validation_errors]}}
    """
    # Target combinations
    target_combos = [
        ("mixed", "mixed"),
        ("xlsindy", "explicit"),
        ("sindy", "explicit")
    ]
    
    # Structure: {noise_level: {combo: [validation_errors]}}
    data = defaultdict(lambda: defaultdict(list))
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            catalog_type = row['catalog_type']
            solution_type = row['solution_type']
            combo = (catalog_type, solution_type)
            
            # Only process target combinations
            if combo not in target_combos:
                continue
            
            # Only consider valid experiments
            valid = row['valid'].strip().lower() == 'true'
            if not valid:
                continue
            
            # Only consider experiments that ran to completion (>= 20s)
            end_simulation_time = row.get('end_simulation_time', '')
            try:
                end_time = float(end_simulation_time)
                if end_time < 20:
                    continue
            except (ValueError, TypeError):
                continue
            
            noise_level = float(row['noise_level'])
            validation_error = row.get('validation_error', '')
            
            # Parse validation error
            if validation_error:
                try:
                    val_error = float(validation_error)
                    data[noise_level][combo].append(val_error)
                except (ValueError, TypeError):
                    pass
    
    return data


def create_plot(data: dict, output_dir: str = "."):
    """
    Create one plot with all systems combined, showing noise levels on x-axis.
    
    Args:
        data: Dictionary with structure {noise_level: {combo: [validation_errors]}}
        output_dir: Directory to save plots
    """
    # Combo names for display
    combo_names = {
        ("mixed", "mixed"): "Mixed",
        ("xlsindy", "explicit"): "XLSINDy",
        ("sindy", "explicit"): "SINDy"
    }
    
    combo_colors = {
        ("mixed", "mixed"): "#3498db",      # Blue
        ("xlsindy", "explicit"): "#e74c3c",  # Red
        ("sindy", "explicit"): "#2ecc71"     # Green
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all noise levels
    all_noise_levels = sorted(data.keys())
    
    # Create single plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    fig.suptitle('Validation Error Comparison - All Systems Combined (Log Scale)', 
                 fontsize=16, fontweight='bold')
    
    # Prepare data for each combo across all noise levels
    combo_list = [("mixed", "mixed"), ("xlsindy", "explicit"), ("sindy", "explicit")]
    
    all_plot_data = []
    all_positions = []
    all_colors = []
    
    # For each combo, add all noise levels with gradient colors
    for combo_idx, combo in enumerate(combo_list):
        # Generate color gradient from light to dark for this combo
        base_color = combo_colors[combo]
        # Convert hex to RGB
        r = int(base_color[1:3], 16) / 255
        g = int(base_color[3:5], 16) / 255
        b = int(base_color[5:7], 16) / 255
        
        for noise_idx, noise_level in enumerate(all_noise_levels):
            noise_data = data.get(noise_level, {})
            
            if combo in noise_data and noise_data[combo]:
                all_plot_data.append(noise_data[combo])
                # Position: combo_idx * 5 + noise_idx (with spacing between combos)
                position = combo_idx * 5 + noise_idx + 1
                all_positions.append(position)
                
                # Create gradient: lighter (0.3) to darker (1.0)
                factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                color = (
                    1 - factor * (1 - r),
                    1 - factor * (1 - g),
                    1 - factor * (1 - b)
                )
                all_colors.append(color)
    
    if not all_plot_data:
        ax.text(0.5, 0.5, 'No valid data', ha='center', va='center', 
               transform=ax.transAxes, fontsize=12, color='gray')
    else:
        # Create box plot
        bp = ax.boxplot(all_plot_data, positions=all_positions, patch_artist=True,
                       showmeans=True, widths=0.6,
                       meanprops=dict(marker='D', markerfacecolor='white', 
                                    markeredgecolor='black', markersize=5),
                       medianprops=dict(color='black', linewidth=2))
        
        # Color the boxes
        for patch, color in zip(bp['boxes'], all_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Set log scale
        ax.set_yscale('log')
        
        # Set x-axis ticks and labels (centered on each group of 4 noise levels)
        x_ticks = [combo_idx * 5 + 2.5 for combo_idx in range(len(combo_list))]
        x_labels = [combo_names[combo] for combo in combo_list]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, fontsize=11)
        ax.set_xlabel('Method (noise levels: 0.0, 0.001, 0.01, 0.1 - only systems converging over full validation period)', fontsize=9)
        
        # Set y-axis
        ax.set_ylabel('Validation Error (log)', fontsize=12, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y', which='both')
        ax.tick_params(axis='y', labelsize=10)
        
        # Add legend for noise levels at top left inside the plot with gradient
        from matplotlib.patches import Patch
        legend_elements = []
        for noise_idx, noise in enumerate(all_noise_levels):
            factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
            gray_val = 1 - factor * 0.6  # Range from light to dark gray
            legend_elements.append(
                Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.7, label=f'Noise: {noise}')
            )
        ax.legend(handles=legend_elements, loc='upper left', fontsize=11, frameon=True)
        
        # Add n_max annotation in bottom right corner
        ax.text(0.98, 0.02, r'$n_{max}=48$', 
               transform=ax.transAxes, fontsize=11, 
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1))
        
        # Add sample count annotations
        for pos, data_points in zip(all_positions, all_plot_data):
            n = len(data_points)
            y_max = max(data_points)
            y_pos = y_max * 1.5
            ax.text(pos, y_pos, f'n={n}', 
                   ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1))
    
    plt.tight_layout()
    
    # Save combined figure
    output_file = output_path / 'validation_comparison_combined_by_system.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved combined plot: {output_file}")
    
    plt.close()


def print_statistics(data: dict):
    """Print summary statistics."""
    
    combo_names = {
        ("mixed", "mixed"): "Mixed",
        ("xlsindy", "explicit"): "XLSINDy",
        ("sindy", "explicit"): "SINDy"
    }
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS - ALL SYSTEMS COMBINED")
    print("=" * 80)
    
    for noise_level in sorted(data.keys()):
        print(f"\nNoise Level: {noise_level}")
        print("-" * 80)
        combo_data = data[noise_level]
        
        for combo in [("mixed", "mixed"), ("xlsindy", "explicit"), ("sindy", "explicit")]:
            if combo in combo_data and combo_data[combo]:
                errors = combo_data[combo]
                print(f"  {combo_names[combo]:10s}: "
                      f"n={len(errors):3d}, "
                      f"mean={np.mean(errors):8.4f}, "
                      f"median={np.median(errors):8.4f}, "
                      f"std={np.std(errors):8.4f}, "
                      f"min={np.min(errors):8.4f}, "
                      f"max={np.max(errors):8.4f}")


def main():
    """Main entry point."""
    # Default path to CSV
    default_csv = Path(__file__).parent.parent.parent / "results_database.csv"
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else str(default_csv)
    output_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).parent.parent.parent / "plots")
    
    if not Path(csv_path).exists():
        print(f"Error: CSV file not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading database from: {csv_path}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Load data
    data = load_data(csv_path)
    
    if not data:
        print("No valid data found!")
        sys.exit(1)
    
    # Print statistics
    print_statistics(data)
    
    # Create plot
    print("\nGenerating plot...")
    create_plot(data, output_dir)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
