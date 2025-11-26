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


def load_data(csv_path: str) -> tuple:
    """
    Load validation errors from the database.
    
    Returns:
        Tuple: (data, success_counts)
        - data: Dictionary {experiment_type: {noise_level: {combo: [validation_errors]}}}
        - success_counts: Dictionary {experiment_type: {noise_level: {combo: {experiment_ids}}}}
    """
    # Target combinations
    target_combos = [
        ("mixed", "mixed"),
        ("xlsindy", "explicit"),
        ("sindy", "explicit")
    ]
    
    # Structure: {experiment_type: {noise_level: {combo: [validation_errors]}}}
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # Track experiment IDs with at least one successful method
    # Structure: {experiment_type: {noise_level: {combo: set(experiment_ids)}}}
    success_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            catalog_type = row['catalog_type']
            solution_type = row['solution_type']
            combo = (catalog_type, solution_type)
            experiment_id = row['experiment_id']
            
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
                    # Track this experiment as successful for this combo
                    success_counts[experiment_type][noise_level][combo].add(experiment_id)
                except (ValueError, TypeError):
                    pass
    
    return data, success_counts


def create_plots(data: dict, success_counts: dict, output_dir: str = "."):
    """
    Create one combined plot with all experiment types as rows.
    
    Args:
        data: Dictionary with structure {experiment_type: {noise_level: {combo: [validation_errors]}}}
        success_counts: Dictionary with structure {experiment_type: {noise_level: {combo: set(experiment_ids)}}}
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
        
        # For each combo, add all noise levels with gradient colors
        for combo_idx, combo in enumerate(combo_list):
            # Generate color gradient from light to dark for this combo
            base_color = combo_colors[combo]
            # Convert hex to RGB
            r = int(base_color[1:3], 16) / 255
            g = int(base_color[3:5], 16) / 255
            b = int(base_color[5:7], 16) / 255
            
            for noise_idx, noise_level in enumerate(all_noise_levels):
                combo_data = noise_data.get(noise_level, {})
                
                if combo in combo_data and combo_data[combo]:
                    all_plot_data.append(combo_data[combo])
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
            
            # Set x-axis ticks and labels (centered on each group of 4 noise levels)
            x_ticks = [combo_idx * 5 + 2.5 for combo_idx in range(len(combo_list))]
            x_labels = [combo_names[combo] for combo in combo_list]
            ax.set_xticks(x_ticks)
            ax.set_xticklabels(x_labels, fontsize=11)
            
            # Only bottom subplot gets x-label
            if row_idx == n_rows - 1:
                ax.set_xlabel('Method (noise levels: 0.0, 0.001, 0.01, 0.1 - only systems converging over full validation period)', fontsize=9)
            
            # Set y-axis
            ax.set_ylabel(f'{pretty_name}\nValidation Error (log)', fontsize=11, fontweight='bold')
            
            # Add grid
            ax.grid(True, alpha=0.3, axis='y', which='both')
            ax.tick_params(axis='y', labelsize=10)
            
            # Add legend only for first subplot showing noise levels with gradient
            if row_idx == 0:
                from matplotlib.patches import Patch
                # Create gradient colors for legend (using gray as neutral)
                legend_elements = []
                for noise_idx, noise in enumerate(all_noise_levels):
                    factor = 0.3 + (0.7 * noise_idx / (len(all_noise_levels) - 1))
                    gray_val = 1 - factor * 0.6  # Range from light to dark gray
                    legend_elements.append(
                        Patch(facecolor=(gray_val, gray_val, gray_val), alpha=0.7, label=f'Noise: {noise}')
                    )
                ax.legend(handles=legend_elements, loc='upper left', fontsize=11, frameon=True)
            
            # Calculate n_max (max success count across all noise levels)
            n_max = 0
            for noise_level in all_noise_levels:
                all_experiment_ids = set()
                for c in combo_list:
                    if c in success_counts[exp_type][noise_level]:
                        all_experiment_ids.update(success_counts[exp_type][noise_level][c])
                n_max = max(n_max, len(all_experiment_ids))
            
            # Add n_max annotation in bottom right corner
            ax.text(0.98, 0.08, f'$n_{{max}}={n_max}$', 
                   transform=ax.transAxes, fontsize=11, 
                   verticalalignment='bottom', horizontalalignment='right',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1))
            
            # Add success rate annotations above each box plot
            plot_idx = 0
            for combo_idx, combo in enumerate(combo_list):
                for noise_idx, noise_level in enumerate(all_noise_levels):
                    combo_data = noise_data.get(noise_level, {})
                    
                    if combo in combo_data and combo_data[combo]:
                        # Get the number of unique experiments that succeeded for this combo+noise
                        n_successful = len(success_counts[exp_type][noise_level][combo])
                        
                        # Calculate total experiments (union of all experiment IDs at this noise level)
                        all_experiment_ids = set()
                        for c in combo_list:
                            if c in success_counts[exp_type][noise_level]:
                                all_experiment_ids.update(success_counts[exp_type][noise_level][c])
                        n_total = len(all_experiment_ids)
                        
                        # Calculate success rate
                        success_rate = (n_successful / n_total * 100) if n_total > 0 else 0
                        
                        pos = all_positions[plot_idx]
                        data_points = all_plot_data[plot_idx]
                        y_max = max(data_points)
                        upper_quartile = np.percentile(data_points, 75)
                        # Use upper_quartile * 2 if max is more than 50x the upper_quartile, otherwise use max * 1.5
                        y_pos = upper_quartile * 2 if y_max > 50 * upper_quartile else y_max * 1.5
                        
                        ax.text(pos, y_pos, f'{success_rate:.0f}%', 
                               ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1))
                        
                        plot_idx += 1
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save combined figure
    output_file = output_path / 'validation_comparison_by_system.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved combined plot: {output_file}")
    
    plt.close()


def export_latex_table(data: dict, success_counts: dict, output_dir: str = "."):
    """
    Export a LaTeX table with average errors and success rates.
    
    Args:
        data: Dictionary with structure {experiment_type: {noise_level: {combo: [validation_errors]}}}
        success_counts: Dictionary with structure {experiment_type: {noise_level: {combo: set(experiment_ids)}}}
        output_dir: Directory to save the table
    """
    combo_names = {
        ("mixed", "mixed"): "Mixed",
        ("xlsindy", "explicit"): "XLSINDy",
        ("sindy", "explicit"): "SINDy"
    }
    
    pretty_names = {
        'cart_pole': 'Cartpole',
        'cart_pole_double': 'Double Pendulum on Cartpole',
        'double_pendulum_pm': 'Double Pendulum'
    }
    
    combo_list = [("mixed", "mixed"), ("xlsindy", "explicit"), ("sindy", "explicit")]
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    latex_file = output_path / 'validation_comparison_table.tex'
    
    with open(latex_file, 'w') as f:
        # Write table header
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\caption{Validation Error Comparison by System and Method}\n")
        f.write("\\label{tab:validation_comparison}\n")
        f.write("\\begin{tabular}{|l|c|c|c|c|c|c|}\n")
        f.write("\\hline\n")
        f.write("\\textbf{System} & \\multicolumn{2}{c|}{\\textbf{Mixed}} & \\multicolumn{2}{c|}{\\textbf{XLSINDy}} & \\multicolumn{2}{c|}{\\textbf{SINDy}} \\\\\n")
        f.write("\\cline{2-7}\n")
        f.write(" & Avg Error & Success & Avg Error & Success & Avg Error & Success \\\\\n")
        f.write("\\hline\n")
        
        # Process each experiment type
        for exp_type in sorted(data.keys()):
            pretty_name = pretty_names.get(exp_type, exp_type)
            noise_data = data[exp_type]
            
            # Collect all errors and success rates across all noise levels
            combo_stats = {}
            for combo in combo_list:
                all_errors = []
                total_successful = set()
                total_experiments = set()
                
                for noise_level in sorted(noise_data.keys()):
                    combo_data = noise_data.get(noise_level, {})
                    
                    if combo in combo_data and combo_data[combo]:
                        all_errors.extend(combo_data[combo])
                        total_successful.update(success_counts[exp_type][noise_level][combo])
                    
                    # Count total experiments at this noise level
                    for c in combo_list:
                        if c in success_counts[exp_type][noise_level]:
                            total_experiments.update(success_counts[exp_type][noise_level][c])
                
                avg_error = np.mean(all_errors) if all_errors else 0
                success_rate = (len(total_successful) / len(total_experiments) * 100) if total_experiments else 0
                combo_stats[combo] = (avg_error, success_rate)
            
            # Write row
            f.write(f"{pretty_name}")
            for combo in combo_list:
                avg_error, success_rate = combo_stats[combo]
                if avg_error > 0:
                    f.write(f" & {avg_error:.2e} & {success_rate:.0f}\\%")
                else:
                    f.write(" & --- & ---")
            f.write(" \\\\\n")
        
        # Write table footer
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")
    
    print(f"Saved LaTeX table: {latex_file}")


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
    data, success_counts = load_data(csv_path)
    
    if not data:
        print("No valid data found!")
        sys.exit(1)
    
    # Print statistics
    print_statistics(data)
    
    # Create plots
    print("\nGenerating plots...")
    create_plots(data, success_counts, output_dir)
    
    # Export LaTeX table
    print("\nGenerating LaTeX table...")
    export_latex_table(data, success_counts, output_dir)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
