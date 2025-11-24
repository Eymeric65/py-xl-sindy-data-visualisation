#!/usr/bin/env python3
"""
Generate mustache (box) plots comparing validation errors across different combinations.

Creates one plot per system type (experiment_type), with subplots for each noise level.
Each subplot shows box plots comparing the three combinations:
- (mixed, mixed)
- (xlsindy, explicit)
- (sindy, explicit)
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
        Dictionary: {experiment_type: {noise_level: {combo: [validation_errors]}}}
    """
    # Target combinations
    target_combos = [
        ("mixed", "mixed"),
        ("xlsindy", "explicit"),
        ("sindy", "explicit")
    ]
    
    # Structure: {experiment_type: {noise_level: {combo: [validation_errors]}}}
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
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
            
            experiment_type = row['experiment_type']
            noise_level = float(row['noise_level'])
            validation_error = row.get('validation_error', '')
            
            # Parse validation error
            if validation_error:
                try:
                    val_error = float(validation_error)
                    data[experiment_type][noise_level][combo].append(val_error)
                except (ValueError, TypeError):
                    pass
    
    return data


def create_plots(data: dict, output_dir: str = "."):
    """
    Create one combined plot with all experiment types as rows.
    
    Args:
        data: Dictionary with structure {experiment_type: {noise_level: {combo: [validation_errors]}}}
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
    
    # Pretty names for experiment types
    pretty_names = {
        'cart_pole': 'Cartpole',
        'cart_pole_double': 'Double Pendulum on Cartpole',
        'double_pendulum_pm': 'Double Pendulum'
    }
    
    # n_max values for each system
    n_max_values = {
        'cart_pole': 12,
        'cart_pole_double': 24,
        'double_pendulum_pm': 12
    }
    
    # Get all experiment types
    exp_types = sorted(data.keys())
    combo_list = [("mixed", "mixed"), ("xlsindy", "explicit"), ("sindy", "explicit")]
    
    n_rows = len(exp_types)
    
    # Create combined figure with subplots
    fig, axes = plt.subplots(n_rows, 1, figsize=(10, 3 * n_rows), squeeze=False)
    
    fig.suptitle('Validation Error Comparison (Log Scale)', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    for row_idx, exp_type in enumerate(exp_types):
        ax = axes[row_idx, 0]
        noise_data = data[exp_type]
        all_noise_levels = sorted(noise_data.keys())
        
        pretty_name = pretty_names.get(exp_type, exp_type)
        
        # Prepare data for each combo across all noise levels
        all_plot_data = []
        all_positions = []
        all_colors = []
        
        # For each noise level, add the three combos
        for noise_idx, noise_level in enumerate(all_noise_levels):
            combo_data = noise_data[noise_level]
            
            for combo_idx, combo in enumerate(combo_list):
                if combo in combo_data and combo_data[combo]:
                    all_plot_data.append(combo_data[combo])
                    # Position: noise_idx * 4 + combo_idx (with spacing between noise levels)
                    position = noise_idx * 4 + combo_idx + 1
                    all_positions.append(position)
                    all_colors.append(combo_colors[combo])
        
        if not all_plot_data:
            ax.text(0.5, 0.5, 'No valid data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='gray')
            ax.set_title(pretty_name, fontsize=14, fontweight='bold')
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
            
            # Set x-axis ticks and labels (centered on each group of 3)
            x_ticks = [noise_idx * 4 + 2 for noise_idx in range(len(all_noise_levels))]
            x_labels = [f'{noise}' for noise in all_noise_levels]
            ax.set_xticks(x_ticks)
            ax.set_xticklabels(x_labels, fontsize=11)
            
            # Only bottom subplot gets x-label
            if row_idx == n_rows - 1:
                ax.set_xlabel('Noise Level (only systems converging over full validation period)', fontsize=10)
            
            # Set y-axis
            ax.set_ylabel(f'{pretty_name}\nValidation Error (log)', fontsize=11, fontweight='bold')
            
            # Add grid
            ax.grid(True, alpha=0.3, axis='y', which='both')
            ax.tick_params(axis='y', labelsize=10)
            
            # Add legend only for second subplot
            if row_idx == 1:
                from matplotlib.patches import Patch
                legend_elements = [
                    Patch(facecolor=combo_colors[combo], alpha=0.7, label=combo_names[combo])
                    for combo in combo_list
                ]
                ax.legend(handles=legend_elements, loc='upper left', fontsize=11, frameon=True)
            
            # Add n_max annotation in bottom right corner
            n_max = n_max_values.get(exp_type, 0)
            ax.text(0.98, 0.08, f'$n_{{max}}={n_max}$', 
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
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save combined figure
    output_file = output_path / 'validation_comparison_all.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved combined plot: {output_file}")
    
    plt.close()


def print_statistics(data: dict):
    """Print summary statistics for each experiment type."""
    
    combo_names = {
        ("mixed", "mixed"): "Mixed",
        ("xlsindy", "explicit"): "XLSINDy",
        ("sindy", "explicit"): "SINDy"
    }
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    for exp_type, noise_data in sorted(data.items()):
        print(f"\n{exp_type.upper()}")
        print("-" * 80)
        
        for noise_level in sorted(noise_data.keys()):
            print(f"\n  Noise Level: {noise_level}")
            combo_data = noise_data[noise_level]
            
            for combo in [("mixed", "mixed"), ("xlsindy", "explicit"), ("sindy", "explicit")]:
                if combo in combo_data and combo_data[combo]:
                    errors = combo_data[combo]
                    print(f"    {combo_names[combo]:10s}: "
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
    
    # Create plots
    print("\nGenerating plots...")
    create_plots(data, output_dir)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
