#!/usr/bin/env python3
"""
Database Analysis and Visualization

This script loads the compiled results database and creates various visualizations
to analyze solution performance, validation errors, and experiment characteristics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
import warnings

# Set up matplotlib and seaborn styling
plt.style.use('default')
sns.set_palette("husl")
warnings.filterwarnings('ignore')


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_database(file_path: str) -> pd.DataFrame:
    """Load the compiled results database."""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Loaded database with {len(df)} solutions from {file_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to load database from {file_path}: {e}")
        raise


def print_database_summary(df: pd.DataFrame) -> None:
    """Print a comprehensive summary of the database."""
    logging.info("=== Database Summary ===")
    logging.info(f"Total solutions: {len(df)}")
    logging.info(f"Total experiments: {df['experiment_id'].nunique()}")
    
    # Summary by key columns
    for col in ['experiment_type', 'solution_type', 'optimizer', 'valid']:
        if col in df.columns:
            logging.info(f"\n{col.replace('_', ' ').title()} distribution:")
            counts = df[col].value_counts()
            for value, count in counts.items():
                percentage = (count / len(df)) * 100
                logging.info(f"  {value}: {count} ({percentage:.1f}%)")
    
    # Noise level distribution
    if 'noise_level' in df.columns:
        logging.info(f"\nNoise level distribution:")
        noise_counts = df['noise_level'].value_counts().sort_index()
        for noise, count in noise_counts.items():
            percentage = (count / len(df)) * 100
            logging.info(f"  {noise}: {count} ({percentage:.1f}%)")
    
    # Valid solutions statistics
    if 'valid' in df.columns:
        valid_count = df['valid'].sum()
        valid_percentage = (valid_count / len(df)) * 100
        logging.info(f"\nValid solutions: {valid_count}/{len(df)} ({valid_percentage:.1f}%)")
        
        if 'validation_error' in df.columns:
            valid_errors = df[df['valid'] == True]['validation_error'].dropna()
            if len(valid_errors) > 0:
                logging.info(f"Validation error statistics (valid solutions only):")
                logging.info(f"  Count: {len(valid_errors)}")
                logging.info(f"  Mean: {valid_errors.mean():.6f}")
                logging.info(f"  Median: {valid_errors.median():.6f}")
                logging.info(f"  Std: {valid_errors.std():.6f}")
                logging.info(f"  Min: {valid_errors.min():.6f}")
                logging.info(f"  Max: {valid_errors.max():.6f}")


def setup_plot_style() -> None:
    """Setup matplotlib plotting style."""
    plt.rcParams.update({
        'figure.figsize': (12, 8),
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16
    })


def create_output_directory(output_dir: str) -> Path:
    """Create output directory for plots."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory: {output_path.absolute()}")
    return output_path


def save_plot(fig: plt.Figure, output_dir: Path, filename: str, 
              dpi: int = 300, bbox_inches: str = 'tight') -> None:
    """Save a plot to the output directory."""
    file_path = output_dir / filename
    fig.savefig(file_path, dpi=dpi, bbox_inches=bbox_inches)
    logging.info(f"Saved plot: {file_path}")


# Placeholder functions for different types of analyses
# These will be implemented based on your specific requirements

def plot_validation_error_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot mustache plots of validation errors in a 3x3 grid: rows=solution_types, cols=experiment_types, grouped by catalog_types."""
    logging.info("Plotting validation error distribution...")
    
    # Filter for valid solutions with validation errors
    valid_df = df[(df['valid'] == True) & (df['validation_error'].notna())].copy()
    
    if len(valid_df) == 0:
        logging.warning("No valid solutions with validation errors found!")
        return
    
    # Get unique types - ensure we have exactly 3 of each for 3x3 grid
    experiment_types = sorted(valid_df['experiment_type'].unique())
    solution_types = sorted(valid_df['solution_type'].unique()) 
    catalog_types = sorted(valid_df['catalog_type'].unique())
    noise_levels = sorted(valid_df['noise_level'].unique())
    
    logging.info(f"Found {len(experiment_types)} experiment types: {experiment_types}")
    logging.info(f"Found {len(solution_types)} solution types: {solution_types}")
    logging.info(f"Found {len(catalog_types)} catalog types: {catalog_types}")
    logging.info(f"Found {len(noise_levels)} noise levels: {noise_levels}")
    
    # Pad lists to ensure 3x3 grid (add None for missing types)
    while len(experiment_types) < 3:
        experiment_types.append(None)
    while len(solution_types) < 3:
        solution_types.append(None)
    
    # Create 3x3 subplot grid
    fig, axes = plt.subplots(3, 3, figsize=(18, 15), sharey=True, sharex=True)
    
    # Color palette for catalog types
    colors = plt.cm.Set2(np.linspace(0, 1, len(catalog_types)))
    catalog_colors = dict(zip(catalog_types, colors))
    
    # Iterate over 3x3 grid: rows=solution_types, cols=experiment_types
    for i, sol_type in enumerate(solution_types):
        for j, exp_type in enumerate(experiment_types):
            ax = axes[i, j]
            
            # Handle empty cells
            if sol_type is None or exp_type is None:
                ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                       ha='center', va='center', fontsize=14, alpha=0.5)
                ax.set_title('Empty')
                continue
            
            # Filter data for this solution type and experiment type (including invalid solutions for total count)
            total_data = df[
                (df['solution_type'] == sol_type) & 
                (df['experiment_type'] == exp_type)
            ]
            
            filtered_data = valid_df[
                (valid_df['solution_type'] == sol_type) & 
                (valid_df['experiment_type'] == exp_type)
            ]
            
            # Calculate total counts for display
            valid_count = len(filtered_data)
            total_count = len(total_data)
            
            if total_count == 0:
                ax.text(0.5, 0.5, f'No data for\n{sol_type}\n{exp_type}', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f'{sol_type} × {exp_type}')
                continue
            
            # Prepare data for box plots
            box_data = []
            box_labels = []
            box_colors = []
            box_positions = []
            
            pos = 0
            # Increase spacing between groups and between individual mustaches
            group_spacing = 2.0  # Space between noise level groups
            mustache_spacing = 0.4  # Space between individual mustaches within a group
            width = 0.3  # Width of each individual mustache plot
            
            for noise_idx, noise in enumerate(noise_levels):
                noise_data = filtered_data[filtered_data['noise_level'] == noise]
                
                if len(noise_data) == 0:
                    continue
                
                for cat_idx, cat_type in enumerate(catalog_types):
                    cat_noise_data = noise_data[noise_data['catalog_type'] == cat_type]
                    
                    if len(cat_noise_data) > 0:
                        validation_errors = cat_noise_data['validation_error'].values
                        box_data.append(validation_errors)
                        box_labels.append(f'{cat_type}\n(n={len(validation_errors)})')
                        box_colors.append(catalog_colors[cat_type])
                        # Position with spacing between individual mustaches
                        box_positions.append(pos + cat_idx * (width + mustache_spacing))
                
                pos += group_spacing  # Move to next noise level group
            
            if not box_data:
                ax.text(0.5, 0.5, f'No valid data for\n{sol_type} × {exp_type}', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f'{sol_type} × {exp_type}')
                continue
            
            # Create box plots with proper width
            bp = ax.boxplot(box_data, positions=box_positions, widths=width, 
                           patch_artist=True, showmeans=True, meanline=True)
            
            # Color the boxes
            for patch, color in zip(bp['boxes'], box_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            # Customize whiskers, caps, medians
            for element in ['whiskers', 'fliers', 'caps']:
                plt.setp(bp[element], color='black', alpha=0.7)
            plt.setp(bp['medians'], color='black', linewidth=2)
            plt.setp(bp['means'], color='red', linewidth=2)
            
            # FIRST: Determine if we need log scale BEFORE setting limits
            use_log_scale = False
            if len(box_data) > 0:
                all_errors = np.concatenate(box_data)
                if len(all_errors) > 1 and all_errors.max() / all_errors.min() > 100:
                    use_log_scale = True
                    ax.set_yscale('log')
            
            # SECOND: Get ACTUAL data range, not matplotlib's auto-extended limits
            if len(box_data) > 0:
                all_errors = np.concatenate(box_data)
                data_min = np.min(all_errors)
                data_max = np.max(all_errors)
            else:
                data_min, data_max = ax.get_ylim()
            
            # THIRD: Calculate reasonable extension based on scale type
            if use_log_scale:
                # For log scale: use small multiplicative factors based on actual data
                # If data goes from 10^-6 to 10^3, extend to ~10^4 (modest extension)
                extended_y_max = data_max * 3  # Only 3x extension, much more reasonable
                extended_y_min = data_min / 2  # Slight extension below too
                
                label_y_positions = []
                for pos in box_positions:
                    label_y_positions.append(data_max * 1.5)  # Position labels at 1.5x data max
            else:
                # For linear scale: extend by adding percentage of data range
                data_range = data_max - data_min
                extended_y_max = data_max + data_range * 0.5  # 50% extension above
                extended_y_min = max(0, data_min - data_range * 0.1)  # Small extension below, but not negative
                
                label_y_positions = []
                for pos in box_positions:
                    label_y_positions.append(data_max + data_range * 0.2)  # Position labels 20% above data
            
            # FOURTH: Set the new limits with reasonable bounds
            ax.set_ylim(extended_y_min, extended_y_max)
            
            # FIFTH: Add count labels with consistent positioning
            for pos, cat_type, label_y in zip(box_positions, [label.split('\n')[0] for label in box_labels], label_y_positions):
                # Count valid and total solutions for this specific catalog type
                cat_valid = len(filtered_data[filtered_data['catalog_type'] == cat_type])
                cat_total = len(total_data[total_data['catalog_type'] == cat_type])
                
                if cat_total > 0:
                    cat_success_rate = (cat_valid / cat_total * 100)
                    label_text = f'{cat_valid}/{cat_total}\n({cat_success_rate:.0f}%)'
                    
                    ax.text(pos, label_y, label_text, ha='center', va='bottom', 
                           fontsize=7, color=catalog_colors[cat_type], weight='bold',
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9, 
                                   edgecolor=catalog_colors[cat_type]))
            
            # Set x-axis labels and ticks with updated spacing
            noise_positions = []
            available_noises = []
            pos = 0
            for noise_idx, noise in enumerate(noise_levels):
                # Check if this noise level has data
                if any(filtered_data['noise_level'] == noise):
                    # Center position for the group of mustaches
                    group_width = (len(catalog_types) - 1) * (width + mustache_spacing)
                    center_pos = pos + group_width / 2
                    noise_positions.append(center_pos)
                    available_noises.append(noise)
                    pos += group_spacing
            
            if noise_positions:
                ax.set_xticks(noise_positions)
                ax.set_xticklabels([f'{noise}' for noise in available_noises], rotation=45)
            
            # Labels and title with valid/total counts
            success_rate = (valid_count / total_count * 100) if total_count > 0 else 0
            ax.set_title(f'{sol_type} × {exp_type.replace("_", " ")}\n{valid_count}/{total_count} solutions ({success_rate:.1f}%)', 
                        fontsize=10)
            
            # Only show x-label on bottom row
            if i == 2:
                ax.set_xlabel('Noise Level', fontsize=10)
            
            # Only show y-label on leftmost column
            if j == 0:
                ax.set_ylabel('Validation Error', fontsize=10)
            
            # Log scale is already set above, no need to repeat
            
            # Grid
            ax.grid(True, alpha=0.3)
    
    # Create legend for catalog types
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=catalog_colors[cat_type], 
                                   alpha=0.7, label=cat_type.replace('_', ' ').title())
                      for cat_type in catalog_types]
    
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), 
               ncol=len(catalog_types), title='Catalog Types')
    
    # Overall title and layout with more space for labels
    fig.suptitle('Validation Error Distribution: Solution Types × Experiment Types (Grouped by Catalog Types)', 
                fontsize=16, y=0.96)
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.5, wspace=0.25)
    
    # Save plot
    save_plot(fig, output_dir, 'validation_error_3x3_grid.png')
    
    # Print summary statistics
    logging.info("Validation Error Summary by Groups:")
    for sol_type in solution_types:
        if sol_type is None:
            continue
        for exp_type in experiment_types:
            if exp_type is None:
                continue
            group_data = valid_df[
                (valid_df['solution_type'] == sol_type) & 
                (valid_df['experiment_type'] == exp_type)
            ]
            if len(group_data) == 0:
                continue
            logging.info(f"\n{sol_type} × {exp_type}:")
            for cat_type in catalog_types:
                cat_data = group_data[group_data['catalog_type'] == cat_type]
                if len(cat_data) > 0:
                    errors = cat_data['validation_error']
                    logging.info(f"  {cat_type}: n={len(errors)}, "
                               f"mean={errors.mean():.6f}, median={errors.median():.6f}")


def plot_success_rate_by_experiment_type(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot success rate (valid solutions) by experiment type."""
    # TODO: Implement success rate by experiment type
    logging.info("Plotting success rate by experiment type...")
    pass


def plot_performance_by_noise_level(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot performance metrics by noise level."""
    # TODO: Implement performance by noise level
    logging.info("Plotting performance by noise level...")
    pass


def plot_optimizer_comparison(df: pd.DataFrame, output_dir: Path) -> None:
    """Compare performance across different optimizers."""
    # TODO: Implement optimizer comparison
    logging.info("Plotting optimizer comparison...")
    pass


def plot_solution_type_analysis(df: pd.DataFrame, output_dir: Path) -> None:
    """Analyze performance by solution type (explicit, implicit, mixed)."""
    # TODO: Implement solution type analysis
    logging.info("Plotting solution type analysis...")
    pass


def plot_correlation_matrix(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot correlation matrix of numerical variables."""
    # TODO: Implement correlation matrix
    logging.info("Plotting correlation matrix...")
    pass


def generate_all_plots(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate all available plots."""
    setup_plot_style()
    
    # List of all plotting functions
    plot_functions = [
        plot_validation_error_distribution,
        plot_success_rate_by_experiment_type,
        plot_performance_by_noise_level,
        plot_optimizer_comparison,
        plot_solution_type_analysis,
        plot_correlation_matrix,
    ]
    
    # Execute each plotting function
    for plot_func in plot_functions:
        try:
            plot_func(df, output_dir)
            plt.close('all')  # Close all figures to free memory
        except Exception as e:
            logging.error(f"Error in {plot_func.__name__}: {e}")


def main():
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze and visualize the compiled results database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--database',
        default='results_database.csv',
        help='Path to the compiled results database CSV file'
    )
    
    parser.add_argument(
        '--output-dir',
        default='plots',
        help='Directory to save generated plots'
    )
    
    parser.add_argument(
        '--plot-type',
        choices=['all', 'validation', 'success', 'noise', 'optimizer', 'solution', 'correlation'],
        default='all',
        help='Type of plot to generate'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-show',
        action='store_true',
        help='Do not display plots interactively'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load database
    try:
        df = load_database(args.database)
    except Exception:
        return 1
    
    # Print summary
    print_database_summary(df)
    
    # Create output directory
    output_dir = create_output_directory(args.output_dir)
    
    # Generate plots based on selection
    if args.plot_type == 'all':
        generate_all_plots(df, output_dir)
    elif args.plot_type == 'validation':
        setup_plot_style()
        plot_validation_error_distribution(df, output_dir)
    elif args.plot_type == 'success':
        setup_plot_style()
        plot_success_rate_by_experiment_type(df, output_dir)
    elif args.plot_type == 'noise':
        setup_plot_style()
        plot_performance_by_noise_level(df, output_dir)
    elif args.plot_type == 'optimizer':
        setup_plot_style()
        plot_optimizer_comparison(df, output_dir)
    elif args.plot_type == 'solution':
        setup_plot_style()
        plot_solution_type_analysis(df, output_dir)
    elif args.plot_type == 'correlation':
        setup_plot_style()
        plot_correlation_matrix(df, output_dir)
    
    # Show plots if requested
    if not args.no_show and args.plot_type != 'all':
        plt.show()
    
    logging.info("Analysis complete!")
    return 0


if __name__ == '__main__':
    exit(main())